"""The chart is always sent cut words: a connector glued onto a word gets its own column."""
from backend.services.nahw import tree_columns


def test_the_api_cuts_a_glued_connector_into_its_own_column():
    # ثُمَّ فَسَوَّىٰهُنَّ سَبْعَ: the chart is always sent cut words, as a typed sentence is,
    # so its one Merged/Split switch works the same on every tab.
    atf = {"role": "حرف عطف", "tone": "ghair_aamil"}
    tree = {"label": "جملة", "children": [
        {"word": 0, "role": "حرف عطف", "tone": "ghair_aamil"},
        {"word": 1, "role": "فعل", "tone": "fil", "prefix_arabic": "فَ",
         "parts": [atf, {"role": "فعل", "tone": "fil"}, {"role": "مفعول به", "tone": "mafool"}]},
        {"word": 2, "role": "مفعول به", "tone": "mafool"},
    ]}
    got = tree_columns.cut({"words": ["ثُمَّ", "فَسَوَّىٰهُنَّ", "سَبْعَ"], "tree": tree})
    assert got["words"] == ["ثُمَّ", "فَ", "سَوَّىٰهُنَّ", "سَبْعَ"]
    assert got["written"] == [0, 1, 1, 2]
    leaves = got["tree"]["children"]
    assert [n["word"] for n in leaves] == [0, 1, 2, 3]
    assert leaves[1] == {"word": 1, "role": "حرف عطف", "tone": "ghair_aamil", "ghair_aamil": True}
    assert [p["role"] for p in leaves[2]["parts"]] == ["فعل", "مفعول به"] and "prefix_arabic" not in leaves[2]

    # وَقَامَ: left with one piece, the rest is named by it alone
    alone = tree_columns.cut({"words": ["وَقَامَ"], "tree": {"children": [
        {"word": 0, "role": "فعل", "prefix_arabic": "وَ", "parts": [atf, {"role": "فعل", "tone": "fil"}]}]}})
    assert alone["tree"]["children"][1] =={"word": 1, "role": "فعل", "tone": "fil", "parts": []}

    # nothing glued: nothing moves
    assert tree_columns.cut({"words": ["ثُمَّ"], "tree": {"children": [tree["children"][0]]}})["written"] == [0]
