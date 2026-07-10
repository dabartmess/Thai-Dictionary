# !/usr/bin/env python3
"""
Thai Dictionary Lookup Tool
===========================
This script accesses Thai dictionary APIs to retrieve Thai translations
and phonetic pronunciations for English words.

Working API: Longdo Dictionary Official (https://dict.longdo.com/mobile.php)

Requirements:
    pip install requests beautifulsoup4

Usage:
    python thai_dict_lookup.py --word apple
    python thai_dict_lookup.py --file words.txt --output output.csv
"""

import csv
import importlib.util
import importlib.util
import os
import re
import sys
import time
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from getthaidictionary import fetchthai_words
from parse_dict_entry import parse_thai_entry
from variables import THAI_VOWELS, THAI_CONSONANTS, TONE_MARKERS
from wordquery import query_longdo

# Longdo Dictionary Official API (HTML format)
LONGDO_MOBILE_URL = "https://dict.longdo.com/mobile.php"
# Request headers to mimic a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


def save_to_csv(results, filename='thai_dictionary.csv'):
    """
    Save translation results to a CSV file.
    """
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)

        # Write header
        writer.writerow(['English Word', 'Thai Word', 'Part of Speech', 'Phonetic Pronunciation', 'Part of Speech'])

        # Sort by English word (alphabetical order)
        sorted_results = sorted(results, key=lambda x: x['english'].lower())

        # Write data
        for result in sorted_results:
            writer.writerow([
                result['english'],
                result['thai'],
                result['phonetic'],
                result["part_of_speech"]
            ])

    print(f"Saved {len(results)} entries to {filename}")


def setup_bs4():
    """Handle BeautifulSoup import across different environments."""
    try:
        from bs4 import BeautifulSoup
        return BeautifulSoup
    except ImportError:
        # Try user site-packages
        user_site = os.path.expanduser('~/.local/lib/python3.12/site-packages')
        if os.path.exists(user_site) and user_site not in sys.path:
            sys.path.insert(0, user_site)
        try:
            from bs4 import BeautifulSoup
            return BeautifulSoup
        except ImportError:
            # Manual load as fallback
            spec = importlib.util.spec_from_file_location(
                'bs4',
                os.path.join(user_site, 'bs4', '__init__.py')
            )
            if spec:
                bs4 = importlib.util.module_from_spec(spec)
                sys.modules['bs4'] = bs4
                spec.loader.exec_module(bs4)
                return bs4.BeautifulSoup
            raise ImportError("BeautifulSoup4 not found. Install: pip install beautifulsoup4")


# ============================================
# API FUNCTIONS
# ============================================

def get_longdo_translation(word):
    """
    Query the official Longdo mobile API for English-to-Thai translation.

    Returns dict with:
        - english: original word
        - thai: Thai translation text
        - phonetic_thai: Thai phonetic (e.g., "/แอ๊ เผิ่ล/")
        - phonetic_ipa: IPA pronunciation (e.g., "/ˈæpəl/")
        - source: API source
    """
    try:
        params = {'search': word}
        response = requests.get(
            LONGDO_MOBILE_URL,
            params=params,
            headers=HEADERS,
            timeout=15
        )

        if response.status_code != 200:
            print(f"Error getting longdo translation for '{word}'")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract phonetic pronunciation from the pronunc-title div
        # phonetic_thai = None
        phonetic_ipa = None

        pronunc_div = soup.find('div', class_='pronunc-title')
        if pronunc_div:
            phonetic_text = pronunc_div.get_text(strip=True)
            # Parse phonetic formats: /แอ๊ เผิ่ล/  /AE1 P AH0 L/  /ˈæpəl/
            phonetic_parts = [p.strip() for p in phonetic_text.split('/') if p.strip()]
            # print(phonetic_parts)

            pattern = re.compile(r"See also:((.*)[,\'\"])*", flags=re.IGNORECASE)
            match1 = re.search(pattern, str(phonetic_parts[1]))
            # print(match1)

            # if len(phonetic_parts) >= 1:
            # phonetic_thai = phonetic_parts[0]
            phonetic_ipa = phonetic_parts[-1]

        # Extract Thai translations from result entries
        thai_translations = []

        # Find all table rows that contain translations
        rows = soup.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            for cell in cells:
                text = cell.get_text(strip=True)
                # Look for Thai text (Thai Unicode range: 0x0E00-0x0E7F)
                if any(ord(c) >= 0x0E00 and ord(c) <= 0x0E7F for c in text):
                    if text and text not in thai_translations:
                        thai_translations.append(text)

        # Get the first/main translation
        thai_word = thai_translations[0] if thai_translations else None

        part_of_speech = ""
        m = re.search(r"\(([^)]+)\)", thai_word)
        if m:
            part_of_speech = m.group(1)
        # print(part_of_speech)

        return {
            'part_of_speech': part_of_speech,
            'english': word,
            'thai': thai_word,
            'phonetic_ipa': phonetic_ipa,
        }

    except Exception as e:
        print(f"Error looking up '{word}': {e}")
        return None


def get_longdo_entry(english1: str, word: str) -> dict:
    """
    Retrieve a Longdo dictionary entry.

    Returns:
    {
        "word": "...",
        "entries": [
            {
                "part_of_speech": "...",
                "english": "...",
                "thai": "...",
                "phonetic": "...",
            },
            ...
        ]
    }
    """

    url = "https://dict.longdo.com/mobile.php"

    r = requests.get(
        url,
        params={"search": word},
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        timeout=15,
    )

    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    result = {
        "word": word,
        "entries": []
    }

    #
    # Longdo changes its HTML occasionally,
    # so this parser is intentionally generic.
    #

    for table in soup.find_all("table"):

        dictionary_name = ""

        caption = table.find("caption")
        if caption:
            dictionary_name = caption.get_text(" ", strip=True)

        for row in table.find_all("tr"):

            cols = row.find_all("td")

            if len(cols) < 2:
                continue

            head = cols[0].get_text(" ", strip=True)
            body = cols[1].get_text(" ", strip=True)
            print("BODY:", body)

            part_of_speech = None

            m = re.search(r"\(([^)]+)\)", body)
            if m:
                part_of_speech = m.group(1)

            # print("'get_londo_entry: english'", english1)
            result["part_of_speech"] = part_of_speech
            result["english"] = english1
            result["thai"] = word
            result["phonetic_ipa"] = thai_to_phonetic(word)

            # print("Result A:", result)

    if not "english" in result:
        print("Result B:", result)
    return result


def lookup_thai_word(word: str) -> dict:
    """
    Lookup a Thai word on Longdo Dictionary.

    Returns:
    {
        "part_of_speech": part_of_speech,
        "thai": <original word>,
        "english": <english translation or None>,
        "phonetic": <phonetic transliteration or None>
    }
    """

    result = {
        "part_of_speech": None,
        "thai": word,
        "english": None,
        "phonetic": None
    }

    url = f"https://dict.longdo.com/search/{quote(word)}"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return result

    soup = BeautifulSoup(response.text, "html.parser")

    text = soup.get_text(" ", strip=True)

    #
    # Look for pronunciation
    #

    m = re.search(
        r'Pronunciation\s*:?\s*([A-Za-z0-9\-\s\'āīūâêôûăǎáàéèíìóòúùəɯɔæ]+)',
        text,
        re.IGNORECASE
    )

    if m:
        result["phonetic"] = m.group(1).strip()

    m = re.search(r"\(([^)]+)\)", text)
    if m:
        part_of_speech = m.group(1)

    #
    # Look for first Thai-English definition
    #

    patterns = [
        r"Thai-English.*?\)\s*(.*?)\s*(?:Syn\.|Ant\.|Example|Hope Dictionary|NECTEC|$)",
        r"\(ศัพท์บัญญัติ\)\s*(.*?)\s*(?:Syn\.|Ant\.|Example|$)",
    ]

    for pattern in patterns:
        m = re.search(pattern, text, re.DOTALL)
        if m:
            print("m.group(1):", m.group(1))
            english = " ".join(m.group(1).split())
            if english:
                result["english"] = english
                break

    return result


def thai_to_phonetic(thai_text):
    """
    Convert Thai text to approximate phonetic pronunciation using
    a simplified transliteration system (similar to Paiboon+/RTGS).

    This is a basic implementation. For production use, consider
    using libraries like pythainlp or external APIs.
    """
    if not thai_text:
        return None

    phonetic = []
    i = 0
    thai_chars = list(thai_text)

    while i < len(thai_chars):
        char = thai_chars[i]
        char_code = ord(char)

        # Skip non-Thai characters
        if char_code < 0x0E00 or char_code > 0x0E7F:
            if char.strip():
                phonetic.append(char)
            i += 1
            continue

        # Check for tone markers
        if char in TONE_MARKERS:
            # Add tone indication
            if phonetic:
                phonetic.append(f"({TONE_MARKERS[char]})")
            i += 1
            continue

        # Check for consonants
        if char in THAI_CONSONANTS:
            phonetic.append(THAI_CONSONANTS[char])
            i += 1
            continue

        # Check for vowels (simplified)
        if char in THAI_VOWELS:
            # Handle leading vowels
            if char in ['เ', 'แ', 'โ', 'ใ', 'ไ']:
                phonetic.append(THAI_VOWELS[char])
            else:
                phonetic.append(THAI_VOWELS[char])
            i += 1
            continue

        # Default: skip unknown characters
        i += 1

    return ''.join(phonetic) if phonetic else None


def fetchthai(english):
    """
    Query the official Longdo mobile API for English-to-Thai translation,
    then parse the result string into its component parts.

    Returns dict with:
        - wordtype: noun, adjective, adverb, etc
        - english: original word
        - thai original entries, including synonyms and antonyms, which will be parsed separately
            - "thai": str,
            - "see_also": list[str],
            - "synonyms": list[str],
            - "antonyms": list[str]
        - phonetic_thai: Thai phonetic (e.g., "/แอ๊ เผิ่ล/")
        - phonetic_ipa: IPA pronunciation (e.g., "/ˈæpəl/")
        - source: API source
    """

    csv = []
    myresult = {}
    with open("dictionary.csv", 'w', encoding='utf-8') as fh:
        max = 3000
        for word in english[:max]:
            myresult = get_longdo_translation(word)
            # print("GetLongDoTranslation:", myresult)
            myenglish = myresult["english"]
            mythai = myresult["thai"]
            myphonetic = myresult["phonetic_ipa"]

            result2 = parse_thai_entry(myenglish, mythai, myphonetic)

            # print("result2['see_also']: ", result2["see_also"])
            # print("result2['english']: ", result2)
            for syn in result2["see_also"]:
                # print("see_also:", syn)
                result3 = lookup_thai_word(syn)
                # result3 = get_longdo_entry(result2["english"], syn)
                print("Result3:", result3)

                if result3["english"] is None:
                    result3["english"] = english

            for syn in result2["synonyms"]:
                # print("SYN:", syn)
                result3 = lookup_thai_word(syn)
                # result3 = get_longdo_translation(syn)

            for ant in result2[r"antonyms"]:
                # print("ANT:", ant)
                result3 = lookup_thai_word(syn)
                # result3 = get_longdo_translation(ant)
            if "english" in result3 and result3["english"] is not None:
                if result3["english"][0] != '[':
                    # print("FOUND!")
                    fh.write(
                        f"\"{result3['english']}\", \"{result3['thai']}\", \"{result3['phonetic'], result3["part_of_speech"]}\"\n")
                    fh.flush()
                    csv.append([result3["english"], result3["thai"], result3["phonetic"], result3["part_of_speech"]])
                else:
                    print("NOT FOUND!")
                    # print(result3["english"])

            time.sleep(0.5)  # Be polite to the API
        fh.close()

    return csv


def fetchenglish():
    url = "https://strommeninc.com/english-words-list-3000-most-common-english-words/"
    response = requests.get(url, timeout=25)
    soup = BeautifulSoup(response.text, 'html.parser')

    tables = soup.find_all('table')
    all_words = []
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            for cell in cells:
                text = cell.get_text().strip()
                if text and text != '-' and len(text) > 1 and text.isalpha():
                    all_words.append(text.lower())

    seen = set()
    unique_words = []
    for word in all_words:
        if word not in seen:
            seen.add(word)
            unique_words.append(word)

    print(f"Total unique words: {len(unique_words)}")
    return unique_words


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    english = fetchenglish()
    print("English:", english)
    wordlist = fetchthai_words()
    # thai = fetchthai(english)
    results_thai = []
    for f in wordlist:
        print("Thai:", f)
        # myresult = get_longdo_entry(english1="", word=f)
        myresult = query_longdo(f)
        if myresult:
            print("MAIN.LONGDO", myresult)
        else:
            print("MAIN.SHORTDO (BAD)", f)
        # myresult["phonetic"] = thai_to_phonetic(f)
        # print("Adding:", myresult)
        results_thai.append(myresult)

    print("Count:", len(results_thai))

    # print(json.dumps(results_thai, indent=2, ensure_ascii=False), flush=True, sep='\n')
    ct = 0

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    english = fetchenglish()
    print("English:", english)
    wordlist = fetchthai_words()
    # thai = fetchthai(english)
    results_thai = []
    for f in wordlist:
        # print("Thai:", f)
        # myresult = get_longdo_entry(english1="", word=f)
        myresult = query_longdo(f)
        if myresult:
            print("MAIN.LONGDO", myresult)
            print("Count:", len(results_thai))
        else:
            print("MAIN.SHORTDO (BAD)", f)
            query_longdo(f)

        # myresult["phonetic"] = thai_to_phonetic(f)
        # print("Adding:", myresult)
        results_thai.append(myresult)

    print("Count:", len(results_thai))

    # print(json.dumps(results_thai, indent=2, ensure_ascii=False), flush=True, sep='\n')
    ct = 0
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
