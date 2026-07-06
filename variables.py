# Independent vowel symbols (very simplified)
THAI_VOWELS = {
    "ะ": "a",
    "ั": "a",
    "า": "aa",
    "ิ": "i",
    "ี": "ii",
    "ึ": "ue",
    "ื": "uee",
    "ุ": "u",
    "ู": "uu",
    "เ": "e",
    "แ": "ae",
    "โ": "o",
    "ใ": "ai",
    "ไ": "ai",
    "ำ": "am",
    "็": "",  # shortener mark
    "ๅ": "aa",
}

# Thai consonants (Royal Thai General System approximation)
THAI_CONSONANTS = {
    "ก": "k", "ข": "kh", "ฃ": "kh", "ค": "kh", "ฅ": "kh", "ฆ": "kh",
    "ง": "ng",
    "จ": "ch", "ฉ": "ch", "ช": "ch", "ซ": "s", "ฌ": "ch",
    "ญ": "y",
    "ฎ": "d", "ฏ": "t",
    "ฐ": "th", "ฑ": "th", "ฒ": "th", "ด": "d", "ต": "t",
    "ถ": "th", "ท": "th", "ธ": "th",
    "น": "n",
    "บ": "b", "ป": "p",
    "ผ": "ph", "ฝ": "f", "พ": "ph", "ฟ": "f", "ภ": "ph",
    "ม": "m",
    "ย": "y",
    "ร": "r",
    "ล": "l",
    "ว": "w",
    "ศ": "s", "ษ": "s", "ส": "s",
    "ห": "h",
    "ฬ": "l",
    "อ": "o",  # vowel carrier/glottal
    "ฮ": "h",
}

# Thai tone marks
TONE_MARKERS = {
    "่": "low",  # mai ek
    "้": "falling",  # mai tho
    "๊": "high",  # mai tri
    "๋": "rising",  # mai chattawa
    "์": "silent",  # thanthakhat (cancels pronunciation)
}
