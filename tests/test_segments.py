from epub2text.segments import _split_offsets


def test_split_offsets_uses_phrasplit_char_offsets_for_abbreviations():
    assert _split_offsets("Dr. Smith is here. She left.", "sentence") == [
        ("Dr. Smith is here.", 0, 18),
        ("She left.", 19, 28),
    ]


def test_split_offsets_uses_phrasplit_char_offsets_for_dotted_acronyms():
    assert _split_offsets("Mr. Smith lives in the U.S.A. He left.", "sentence") == [
        ("Mr. Smith lives in the U.S.A.", 0, 29),
        ("He left.", 30, 38),
    ]
