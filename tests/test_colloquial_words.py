from backend.services.colloquial.wordcheck import forms_of, known_forms, missing, skeleton


def test_chat_and_scholarly_spellings_meet():
    assert skeleton("marḥaba") == skeleton("mar7aba") == "mr7b"
    assert skeleton("ʔakīd") == skeleton("akeed")
    assert skeleton("xamīr") == skeleton("khameer")


def test_prefix_and_ending_are_tried():
    assert skeleton("kīf") in forms_of("keefak")
    assert skeleton("bāb") in forms_of("wil-baab")


def test_a_blank_word_matches_nothing():
    assert forms_of("") == set()


def test_a_word_in_the_reference_is_not_missing():
    assert known_forms("ddda")
    assert missing(["keefak", "zzzqxq"]) == ["zzzqxq"]
