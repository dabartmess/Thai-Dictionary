#!/usr/bin/env python3
"""
Parse dictionary entry strings into structured data.

Extracts:
- english: the English word
- thai: the full Thai translation text
- thai_base: the base Thai translation (before See also/Syn/Ant markers)
- seealso: list of Thai "See also" terms (after "See also:")
- syn: list of synonyms (after "Syn.")
- ant: list of antonyms (after "Ant.")
- phonetic: phonetic transcription
"""

import json

test = {'english': 'abandon', 'thai': '(n) การปลดปล่อย,See also:การปลดปล่อยอารมณ์', 'phonetic_thai': 'เออะ แบ๊น เดิ่น',
        'phonetic_ipa': 'əbˈændən', 'source': 'Longdo'}

import re


def parse_thai_entry(english, text, phonetic):
    """
    Parse a Thai dictionary entry.

    Returns:
        {
            "thai": str,
            "see_also": list[str],
            "synonyms": list[str],
            "antonyms": list[str],
            "english": str,
        }
    """
    result = {
        "thai": "",
        "see_also": [],
        "synonyms": [],
        "antonyms": [],
        "english": [],
        "part_of_speech": [],
    }

    print("parse_thai_entry: english:", english)
    result["english"] = english

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

    # Primary Thai word
    m = re.search(r'\)\s*([^,]+)', text)
    if m:
        result["thai"] = m.group(1).strip()

    # See also
    m = re.search(r'See also:([^,]+(?:,[^,]+)*?)(?=,Syn\.|,Ant\.|$)', text)
    if m:
        result["see_also"] = [
            w.strip() for w in m.group(1).split(",") if w.strip()
        ]
    print("see_also:", result["see_also"])

    # Synonyms
    m = re.search(r'Syn\.([^,]+(?:,[^,]+)*?)(?=,Ant\.|$)', text)
    if m:
        result["synonyms"] = [
            w.strip() for w in m.group(1).split(",") if w.strip()
        ]

    # Antonyms
    m = re.search(r'Ant\.([^,]+(?:,[^,]+)*)', text)
    if m:
        result["antonyms"] = [
            w.strip() for w in m.group(1).split(",") if w.strip()
        ]

    m = re.search(r"\(([^)]+)\)", text)
    if m:
        part_of_speech = m.group(1)

    result["phonetic"] = phonetic

    if not "english" in result:
        print("English word:", english)
        result["english"] = english

    return result


# Example usage
if __name__ == "__main__":
    test_string = {'english': "ability",
                   "thai": "(n) ความสามารถ,See also:ความมีฝีมือ,ความมีทักษะ,สมรรถภาพ,Syn.capability,expertness,Ant.inability,unfitness",
                   'phonetic': "əbˈɪlətˌiː"}

    result = parse_thai_entry(test_string['english'], test_string['thai'], test_string['phonetic'])
    print("Parsed Result:", json.dumps(result, ensure_ascii=False, indent=2))
