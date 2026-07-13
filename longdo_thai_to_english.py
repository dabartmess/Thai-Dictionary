"""
Longdo Dictionary Thai-to-English Lookup
==========================================

This module provides functions to look up English translations
for Thai words using the Longdo Dictionary API.

Official API: https://dict.longdo.com/mobile.php?search=<word>
Returns HTML - requires parsing to extract English definitions.

Unofficial JSON API (easier to use):
http://longdo-dict-unofficial-api.herokuapp.com/search/<query>
Returns structured JSON with definitions.
"""

import re
from html.parser import HTMLParser
from typing import List, Dict, Union

import requests


class LongdoHTMLParser(HTMLParser):
    """Parse Longdo mobile.php HTML response to extract definitions."""

    def __init__(self):
        super().__init__()
        self.in_definition = False
        self.in_word = False
        self.in_pos = False
        self.current_tag = None
        self.definitions = []
        self.current_def = {"word": "", "pos": "", "meanings": []}
        self.text_buffer = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        self.current_tag = tag

        # Look for definition blocks (varies by Longdo HTML structure)
        if tag == "div" and attrs_dict.get("class") in ["search-result", "result", "def"]:
            self.in_definition = True
            self.current_def = {"word": "", "pos": "", "meanings": []}

    def handle_endtag(self, tag):
        if tag == "div" and self.in_definition:
            self.in_definition = False
            if self.current_def["meanings"]:
                self.definitions.append(self.current_def)

    def handle_data(self, data):
        if self.in_definition:
            self.text_buffer += data.strip()

    def get_definitions(self) -> List[Dict]:
        return self.definitions


def lookup_longdo_official(thai_word: str) -> List[Dict[str, str]]:
    """
    Look up a Thai word using Longdo's official mobile API.

    Args:
        thai_word: Thai word to look up (e.g., "น้ำ", "สวัสดี")

    Returns:
        List of dictionaries with keys: 'word', 'pos', 'definition'

    Example:
        >>> results = lookup_longdo_official("น้ำ")
        >>> print(results[0]['definition'])
        'water'
    """
    url = f"https://dict.longdo.com/mobile.php?search={requests.utils.quote(thai_word)}"

    try:
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()

        html = response.text
        definitions = []

        # Parse HTML using regex patterns for Longdo's mobile output
        # Pattern 1: Look for definition blocks with English text
        # Longdo typically shows: word [POS] definition

        # Extract all text content and clean it
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Look for dictionary entries
        # Typical format: word [part of speech] English definition
        entry_pattern = r'([^\[]+)\s*\[([^\]]+)\]\s*([^\n]+)'
        matches = re.findall(entry_pattern, text)

        for match in matches:
            word, pos, definition = match
            word = word.strip()
            pos = pos.strip()
            definition = definition.strip()

            # Filter for entries that have English definitions
            # (Thai words with English translations)
            if word and definition:
                # Check if the searched word appears in the entry
                if thai_word in word or word in thai_word:
                    definitions.append({
                        'word': word,
                        'pos': pos,
                        'definition': definition
                    })

        return definitions if definitions else [{"word": thai_word, "pos": "N/A", "definition": "No results found"}]

    except requests.RequestException as e:
        return [{"word": thai_word, "pos": "ERROR", "definition": f"Request failed: {str(e)}"}]


def lookup_longdo_unofficial(thai_word: str) -> List[Dict[str, Union[str, List[str]]]]:
    """
    Look up a Thai word using the unofficial Longdo JSON API.

    Args:
        thai_word: Thai word to look up (e.g., "น้ำ", "สวัสดี")

    Returns:
        List of dictionaries with keys: 'term', 'pos', 'def', 'also', 'syn'

    Example:
        >>> results = lookup_longdo_unofficial("น้ำ")
        >>> print(results[0]['def'])
        ['water']
    """
    url = f"http://longdo-dict-unofficial-api.herokuapp.com/search/{requests.utils.quote(thai_word)}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get("err"):
            return [{"term": thai_word, "pos": "ERROR", "def": ["API error"], "also": [], "syn": []}]

        results = []

        # The unofficial API returns results organized by dictionary source
        for dict_name, entries in data.get("result", {}).items():
            if "TH-EN" in dict_name or "Lexitron" in dict_name:
                for entry in entries:
                    results.append({
                        "term": entry.get("term", thai_word),
                        "pos": entry.get("pos", "N/A"),
                        "def": entry.get("def", []),
                        "also": entry.get("also", []),
                        "syn": entry.get("syn", [])
                    })

        return results if results else [
            {"term": thai_word, "pos": "N/A", "def": ["No results found"], "also": [], "syn": []}]

    except requests.RequestException as e:
        return [{"term": thai_word, "pos": "ERROR", "def": [f"Request failed: {str(e)}"], "also": [], "syn": []}]


def find_english_from_thai(thai_word: str, use_unofficial: bool = True) -> str:
    """
    Simple function to get the primary English translation of a Thai word.

    Args:
        thai_word: Thai word to translate (e.g., "น้ำ", "สวัสดี", "กิน")
        use_unofficial: Whether to use the unofficial JSON API (faster, structured)
                        or the official HTML API (more reliable, always available)

    Returns:
        Primary English translation as a string

    Example:
        >>> find_english_from_thai("น้ำ")
        'water'
        >>> find_english_from_thai("สวัสดี")
        'hello'
        >>> find_english_from_thai("กิน")
        'to eat'
    """
    if use_unofficial:
        results = lookup_longdo_unofficial(thai_word)
        if results and results[0].get("def"):
            return results[0]["def"][0] if results[0]["def"] else thai_word
    else:
        results = lookup_longdo_official(thai_word)
        if results and results[0].get("definition"):
            return results[0]["definition"]

    return thai_word  # Return original if no translation found


def find_english_from_thai_detailed(thai_word: str, use_unofficial: bool = True) -> Dict:
    """
    Get detailed translation information for a Thai word.

    Args:
        thai_word: Thai word to translate
        use_unofficial: Which API to use

    Returns:
        Dictionary with all available translation data

    Example:
        >>> result = find_english_from_thai_detailed("น้ำ")
        >>> print(result)
        {
            'thai_word': 'น้ำ',
            'english_primary': 'water',
            'all_definitions': ['water', 'liquid', 'juice'],
            'part_of_speech': 'N',
            'synonyms': ['liquid', 'fluid'],
            'related': ['น้ำเปล่า', 'น้ำดื่ม']
        }
    """
    if use_unofficial:
        results = lookup_longdo_unofficial(thai_word)
        if not results:
            return {"thai_word": thai_word, "error": "No results found"}

        primary = results[0]
        all_defs = []
        for r in results:
            all_defs.extend(r.get("def", []))

        return {
            "thai_word": thai_word,
            "english_primary": primary.get("def", [thai_word])[0] if primary.get("def") else thai_word,
            "all_definitions": list(dict.fromkeys(all_defs)),  # Remove duplicates, preserve order
            "part_of_speech": primary.get("pos", "N/A"),
            "synonyms": primary.get("syn", []),
            "related": primary.get("also", [])
        }
    else:
        results = lookup_longdo_official(thai_word)
        if not results:
            return {"thai_word": thai_word, "error": "No results found"}

        primary = results[0]
        all_defs = [r["definition"] for r in results if "definition" in r]

        return {
            "thai_word": thai_word,
            "english_primary": primary.get("definition", thai_word),
            "all_definitions": list(dict.fromkeys(all_defs)),
            "part_of_speech": primary.get("pos", "N/A"),
            "synonyms": [],
            "related": []
        }


# ============== BATCH PROCESSING ==============

def batch_translate_thai_to_english(thai_words: List[str], use_unofficial: bool = True) -> Dict[str, str]:
    """
    Translate multiple Thai words to English in one call.

    Args:
        thai_words: List of Thai words to translate
        use_unofficial: Which API to use

    Returns:
        Dictionary mapping Thai words to their English translations

    Example:
        >>> words = ["น้ำ", "สวัสดี", "กิน", "รัก"]
        >>> batch_translate_thai_to_english(words)
        {'น้ำ': 'water', 'สวัสดี': 'hello', 'กิน': 'to eat', 'รัก': 'to love'}
    """
    results = {}
    for word in thai_words:
        results[word] = find_english_from_thai(word, use_unofficial)
    return results


# ============== DEMO / TESTING ==============

if __name__ == "__main__":
    # Test with sample Thai words
    test_words = ["น้ำ", "สวัสดี", "กิน", "รัก", "บ้าน", "รถ", "ใหญ่"]

    print("=" * 60)
    print("Longdo Dictionary Thai → English Lookup")
    print("=" * 60)

    for word in test_words:
        print(f"\nThai word: {word}")
        print("-" * 40)

        # Simple lookup
        english = find_english_from_thai(word)
        print(f"  English: {english}")

        # Detailed lookup
        detailed = find_english_from_thai_detailed(word)
        print(f"  POS: {detailed.get('part_of_speech', 'N/A')}")
        print(f"  All definitions: {detailed.get('all_definitions', [])}")
        if detailed.get('synonyms'):
            print(f"  Synonyms: {detailed['synonyms']}")

    print("\n" + "=" * 60)
    print("Batch Translation:")
    print("=" * 60)
    batch_results = batch_translate_thai_to_english(test_words)
    for thai, eng in batch_results.items():
        print(f"  {thai} → {eng}")
