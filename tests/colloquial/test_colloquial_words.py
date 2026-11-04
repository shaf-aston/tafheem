import urllib.error

import pytest

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
    # The reference downloads from its publisher on first use; their server being down is not our failure.
    try:
        assert known_forms("ddda")
    except (urllib.error.URLError, TimeoutError) as down:
        pytest.skip(f"reference server unreachable: {down}")
    assert missing(["keefak", "zzzqxq"]) == ["zzzqxq"]


def test_every_picture_exists_is_credited_and_is_not_repeated_in_a_topic():
    """Shipped data: no dead picture link, no uncredited photo, no two words of a topic sharing one picture."""
    import json
    from collections import defaultdict
    from backend.config import data_path

    root = data_path("colloquial_dir")
    spine = json.loads((root / "spine.json").read_text(encoding="utf-8"))
    words = json.loads((root / "words.json").read_text(encoding="utf-8"))["words"]
    credits: dict[str, dict] = {}

    def credited(image: str) -> bool:
        folder, name = image.split("/", 1)
        if folder not in credits:
            file = root / "images" / folder / "attribution.json"
            credits[folder] = json.loads(file.read_text(encoding="utf-8")) if file.exists() else {}
        return "*" in credits[folder] or name in credits[folder] or name in credits[folder].get("files", {})

    for key, word in words.items():
        if word.get("image"):
            assert (root / "images" / word["image"]).exists(), f"{key}: {word['image']} is missing"
            assert credited(word["image"]), f"{key}: {word['image']} has no credit"
    for unit in spine["units"]:
        for lesson in unit["lessons"]:
            for phrase in lesson["phrases"]:
                if phrase.get("image"):
                    assert (root / "images" / phrase["image"]).exists(), f"{phrase['slot']}: {phrase['image']} is missing"
                    assert credited(phrase["image"]), f"{phrase['slot']}: {phrase['image']} has no credit"
            seen = defaultdict(list)
            for key in lesson.get("words", []):
                if words.get(key, {}).get("image"):
                    seen[words[key]["image"]].append(key)
            shared = {image: keys for image, keys in seen.items() if len(keys) > 1}
            assert not shared, f"{unit['unit']}/{lesson['lesson']} repeats a picture: {shared}"
