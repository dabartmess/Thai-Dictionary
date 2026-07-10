import json
import re

import requests


def query_longdo(word):
    """
    Query Longdo Dictionary (unofficial) for a Thai or English word.

    Args:
        word: Thai or English word to search

    Returns:
        dict: JSON-compatible dictionary with:
            - thai_word: The Thai word (if input was Thai)
            - english_word: The English word (if input was English)
            - query_word: Original search term
            - phonetic_ipa: IPA phonetic transcription (best available)
            - phonetic_cmu: CMU Arpabet pronunciation
            - thai_reading: Thai phonetic reading (for English words)
            - part_of_speech: Combined parts of speech
            - translations: List of definition entries
    """
    url = "https://dict.longdo.com/mobile.php"
    params = {"search": word}

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        return {
            "thai_word": word if _is_thai(word) else None,
            "english_word": None if _is_thai(word) else word,
            "query_word": word,
            "phonetic_ipa": None,
            "phonetic_cmu": None,
            "thai_reading": None,
            "part_of_speech": None,
            "translations": [],
            "error": str(e)
        }

    # Extract pronunciation data from embedded JavaScript
    phonetic_ipa, phonetic_cmu, thai_reading = _extract_pronunciations(html)

    # Fallback: Extract IPA from Volubilis dictionary [phonetic] notation
    volubilis_ipa = _extract_volubilis_ipa(html)
    final_ipa = phonetic_ipa or volubilis_ipa or phonetic_cmu
    # print("Final IPA:", final_ipa)

    # Parse dictionary entries from HTML tables
    translations, all_pos = _parse_entries(html, word, final_ipa)
    # print("Translation:", json.dumps(translations, ensure_ascii=False, indent=2))

    is_thai = _is_thai(word)

    # return {
    #     "eng_or_thai": is_thai,
    #     "thai_word": word if is_thai else None,
    #     "english_word": None if is_thai else word,
    #     "query_word": word,
    #     "phonetic_ipa": final_ipa,
    #     "phonetic_cmu": phonetic_cmu,
    #     "thai_reading": thai_reading,
    #     "part_of_speech": ", ".join(sorted(all_pos)) if all_pos else None,
    #     # "translations": translations[:10]  # Limit to first 10 entries
    #     "translations": translations
    # }

    return translations


def _is_thai(text):
    """Check if text contains Thai characters."""
    return bool(re.search(r'[\u0e00-\u0e7f]', text))


def _extract_pronunciations(html):
    """Extract pronunciation data from the JavaScript array in HTML."""
    phonetic_ipa = None
    phonetic_cmu = None
    thai_reading = None

    match = re.search(r'const resPronuncs = (\[.*?\]);', html, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            for p in data:
                if p.get('type') == 'ipa' and not phonetic_ipa:
                    phonetic_ipa = p.get('text', '')
                elif p.get('type') == 'cmu' and not phonetic_cmu:
                    phonetic_cmu = p.get('text', '')
                elif p.get('type') == 'thai_reading' and not thai_reading:
                    thai_reading = p.get('text', '')
                    print("Thai reading:", thai_reading)
        except json.JSONDecodeError:
            pass

    return phonetic_ipa, phonetic_cmu, thai_reading


def _extract_volubilis_ipa(html):
    """Extract phonetic notation from Volubilis dictionary entries."""
    # Match phonetic notation like [sawatdī], [hēllō], etc.
    match = re.search(
        r'\[([a-zA-Zāīūēōṭḍṇṃḥśṣñṅ\.\s\u02c8\u02cc\u0259\u028a\u025b\u026a\u0254\u00e6\u028c\u0251\u0252\u026b\u0275\u0283\u0292\u03b8\u00f0\u014b\u02a7\u02a6]+)\]',
        html)
    return match.group(1).strip() if match else None


def _parse_entries(html, query_word, final_ipa):
    """Parse dictionary entries from HTML table structure."""
    translations = []
    all_pos = set()

    # Pattern: <b>Dictionary Name</b> followed by <table class='result-table'>...</table>
    dict_pattern = r'<b>(.*?)</b>(?:<br/>)?<table class=\'result-table\'>(.*?)</table>'
    dict_matches = re.findall(dict_pattern, html, re.DOTALL)
    tmp = {}
    eng_trans = None
    tmp_phonetic_ipa = final_ipa
    # print("final_ipa:", tmp_phonetic_ipa, final_ipa)

    for dict_name, table_content in dict_matches:
        dict_name = re.sub(r'<[^>]+>', '', dict_name).strip()

        # Skip unapproved/unsafe dictionaries
        if 'ระวัง' in dict_name or 'unapproved' in dict_name.lower():
            continue

        # Parse table rows
        rows = re.findall(r'<tr>(.*?)</tr>', table_content, re.DOTALL)

        for row in rows:
            tds = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
            if len(tds) < 2:
                continue

            word_cell, def_cell = tds[0], tds[1]

            # Extract word from cell
            word_match = re.search(r'<b>(.*?)</b>', word_cell)
            if not word_match:
                word_match = re.search(r'>([^<]+)</a>', word_cell)
            entry_word = word_match.group(1).strip() if word_match else query_word

            # Extract part of speech: (n), (v), (adj), (int), etc.
            # pos_match = re.match(r'\s*\(([^)]+)\)\s*', def_cell)
            pos_match = re.match(r'^\(([a-zA-Z]*)\)', def_cell)
            pos = pos_match.group(1).strip() if pos_match else None
            if pos and len(pos) < 20:  # Filter out false positives
                all_pos.add(pos)

            # Clean HTML tags from definition
            clean_def = re.sub(r'<[^>]+>', ' ', def_cell)
            clean_def = re.sub(r'\s+', ' ', clean_def).strip()

            # Extract English translation
            eng_trans = _extract_english_translation(clean_def, dict_name)
            # Extract phonetic from entry [phonetic] notation
            entry_phonetic = None
            phonetic_match = re.search(r'\[([^\]]+)\]', def_cell)
            if phonetic_match:
                entry_phonetic = phonetic_match.group(1).strip()
                if (not tmp_phonetic_ipa and entry_phonetic):
                    tmp_phonetic_ipa = entry_phonetic

        if _is_thai(def_cell):
            tmp['word'] = entry_word
            if all_pos:
                tmp['part_of_speech'] = str(all_pos)
            if tmp_phonetic_ipa or entry_phonetic:
                tmp['phonetic'] = tmp_phonetic_ipa
            if eng_trans:
                tmp['english_translation'] = eng_trans

            # translations.append({
            #     'dictionary': dict_name,
            #     'word': entry_word,
            #     'part_of_speech': pos,
            #     'definition': clean_def,
            #     'english_translation': eng_trans,
            #     'phonetic': entry_phonetic,
            #     'example': example
            # })

    # return translations, all_pos
    return tmp, all_pos


def _extract_english_translation(clean_def, dict_name):
    """Extract English translation based on dictionary type."""
    eng_trans = None

    # print("Dict:", dict_name)
    # print("clean_def:", clean_def)

    if 'EN:' in clean_def:
        # Volubilis format: EN: word1 ; word2
        eng_match = re.search(r'EN:\s*([^;]+)', clean_def)
        # eng_match = re.search(r'EN:([\p{P}\p{S}]+);', clean_def)
        if eng_match:
            eng_trans = eng_match.group(1).strip()
    elif 'TH-EN' in dict_name or 'Volubilis' in dict_name:
        # Thai-English dictionary: definition is English
        eng_match = re.search(r'\)\s*([A-Za-z\s-]+)', clean_def)
        if eng_match:
            eng_trans = eng_match.group(1).strip().rstrip(',').strip()
    # else:
    #     # English-Thai dictionary: definition is Thai
    #     eng_match = re.search(r'\)\s*([\u0e00-\u0e7f\s]+)', clean_def)
    #     if eng_match:
    #         eng_trans = eng_match.group(1).strip()

    return eng_trans


# Example usage
if __name__ == "__main__":
    # Test with Thai word
    print("=" * 60)
    print("Querying Thai word: สวัสดี")
    print("=" * 60)
    result = query_longdo("สวัสดี")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    print("\n" + "=" * 60)
    print("Querying Thai word: ห้อง")
    print("=" * 60)
    result2 = query_longdo("ห้อง")
    print(json.dumps(result2, ensure_ascii=False, indent=2))
