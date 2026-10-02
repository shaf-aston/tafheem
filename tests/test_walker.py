"""The naming tree is data, so the walker is tested on tiny trees of its own."""
import pytest

from backend.services.nahw_book import book_path
from backend.services.syntax import walker
from backend.services.syntax.facts import AXES


def leaf(branch, answer, role="حرف"):
    """`else` as the answer makes the one fall-through child."""
    pick = {"else": True} if answer == "else" else {"is": answer}
    return {"branch": branch, "book": "1.1 p1", "role": role, **pick}


def root(*children):
    return {"branch": "root", "book": "1.1 p1", "split": "kind", "children": list(children)}


def test_real_tree_is_valid():
    walker.validate(walker.load())


def test_rejects_unknown_axis():
    with pytest.raises(ValueError, match="unknown axis"):
        walker.validate({**root(leaf("a", "harf")), "split": "nope"})


def test_rejects_value_outside_axis():
    with pytest.raises(ValueError, match="not one of"):
        walker.validate(root(leaf("a", "dual")))


def test_rejects_duplicate_value():
    with pytest.raises(ValueError, match="same answer"):
        walker.validate(root(leaf("a", "harf"), leaf("b", "harf", "فعل")))


def test_rejects_two_elses():
    with pytest.raises(ValueError, match="more than one"):
        walker.validate(root(leaf("a", "else"), leaf("b", "else", "فعل")))


def test_rejects_unknown_role_and_both_or_neither():
    with pytest.raises(ValueError, match="unknown role"):
        walker.validate(root(leaf("a", "harf", "not a role")))
    with pytest.raises(ValueError, match="exactly one"):
        walker.validate(root({"branch": "a", "book": "1.1 p1", "is": "harf"}))


def test_walk_reaches_leaf():
    tree = root(leaf("h", "harf"), leaf("f", "fil", "فعل"))
    assert walker.walk({"kind": "fil"}, tree) == ("فعل", ["root", "f"], "1.1 p1")


def test_walk_falls_to_else():
    tree = root(leaf("h", "harf"), leaf("rest", "else", "فعل"))
    assert walker.walk({"kind": "ism"}, tree) == ("فعل", ["root", "rest"], "1.1 p1")


def test_walk_no_match_is_none():
    assert walker.walk({"kind": "ism"}, root(leaf("h", "harf"))) is None
    assert walker.walk({"kind": "ism", "follows": "none", "governor": "none", "slot": "none"}) is None  # a word with another governor is not filled in yet


def test_a_child_may_take_several_answers():
    group = {"branch": "g", "book": "1.1 p1", "is": ["harf", "fil"], "split": "kind",
             "children": [leaf("h", "harf"), leaf("f", "fil", "فعل")]}
    tree = root(group, leaf("rest", "else", "فعل"))
    walker.validate(tree)
    assert walker.walk({"kind": "fil"}, tree) == ("فعل", ["root", "g", "f"], "1.1 p1")
    assert walker.walk({"kind": "ism"}, tree) == ("فعل", ["root", "rest"], "1.1 p1")


def test_rejects_listed_answer_outside_axis_or_repeated_across_children():
    with pytest.raises(ValueError, match="not one of"):
        walker.validate(root({**leaf("a", "harf"), "is": ["harf", "dual"]}))
    with pytest.raises(ValueError, match="same answer"):
        walker.validate(root({**leaf("a", "harf"), "is": ["harf", "fil"]}, leaf("b", "fil", "فعل")))


def test_rejects_a_nested_split_naming_an_answer_its_parent_did_not_take():
    group = {"branch": "g", "book": "1.1 p1", "is": "harf", "split": "kind", "children": [leaf("f", "fil", "فعل")]}
    with pytest.raises(ValueError, match="not one of"):
        walker.validate(root(group, leaf("rest", "else", "فعل")))


def test_rejects_empty_children_a_non_true_else_and_an_else_with_nothing_left():
    with pytest.raises(ValueError, match="empty"):
        walker.validate(root({"branch": "g", "book": "1.1 p1", "is": "harf", "split": "kind", "children": []}))
    with pytest.raises(ValueError, match="must be true"):
        walker.validate(root({"branch": "a", "book": "1.1 p1", "role": "حرف", "else": 1}))
    with pytest.raises(ValueError, match="every answer"):
        walker.validate(root(leaf("a", "harf"), leaf("b", "fil", "فعل"), leaf("c", "ism"), leaf("rest", "else")))


# Where the real tree has no child for an answer its axis can give, a word stops unnamed
# (a gap, never a guess). Each stop is listed with the book reason; a new one is a new
# hole and must be argued for here or filled in naming_tree.json.
VERB_ONLY = {"object", "second_object", "absolute", "place_time"}
ALLOWED_STOPS = {
    ("إن وأخواتها", "slot"): (VERB_ONLY | {"specification", "none"},
                              "إن takes an اسم and a خبر; the particle has no object, and the other places are a verb's"),
    ("كان وأخواتها", "slot"): (VERB_ONLY | {"specification", "none"},
                               "كان names its اسم and خبر; an object of it stays unnamed"),
    ("كاد وأخواتها", "slot"): (VERB_ONLY | {"specification", "none"},
                               "كاد names its اسم and خبر; an object of it stays unnamed"),
    ("ظن وأخواتها", "voice"): ({"passive", "none"},
                               "a passive ظن has no places of its own (none cannot occur: ظن is a verb)"),
    ("ظن المبنية للمعلوم", "slot"): ({"predicate", "absolute", "place_time", "none"},
                                     "ظن's places are its doer and two objects; a khabar or an adverb is not one"),
    ("الفعل", "slot"): ({"predicate", "none"}, "a khabar is not a place a verb gives"),
    ("الفاعل ونائبه", "voice"): ({"none"}, "a doer always has its verb above it"),
    ("ما له عامل آخر", "slot"): (VERB_ONLY | {"none"},
                                 "only a verb gives those places; none is a word the nominal sentence cannot place"),
}


def dead_ends(node, path=(), left=None):
    """(branch, axis, answer) for every answer a split's axis can give that no child takes."""
    left = left or {}
    if "role" in node:
        return
    axis = node["split"]
    allowed = left.get(axis, AXES[axis][0])
    taken = {a for c in node["children"] if "is" in c for a in walker._answers(c)}
    rest = tuple(a for a in allowed if a not in taken)
    if not any("else" in c for c in node["children"]):
        yield from ((node["branch"], axis, a) for a in rest)
    for c in node["children"]:
        yield from dead_ends(c, path, {**left, axis: tuple(walker._answers(c)) if "is" in c else rest})


def test_every_answer_reaches_a_leaf_except_the_listed_stops():
    stops = {}
    for branch, axis, answer in dead_ends(walker.load()):
        stops.setdefault((branch, axis), set()).add(answer)
    print({key: sorted(value) for key, value in stops.items()})
    assert stops == {key: answers for key, (answers, _) in ALLOWED_STOPS.items()}


def test_rejects_a_book_reference_without_section_and_page():
    with pytest.raises(ValueError, match="like '3.1 p60'"):
        walker.validate(root({**leaf("a", "harf"), "book": "Tasheel"}))


def test_the_proof_line_names_the_branches_below_kalima_once_each():
    said = book_path(["كلمة", "فعل", "فعل"], "1.2 p2")
    assert said.startswith("فعل (") and "1.2" in said and "2" in said
    said = book_path(["كلمة", "اسم", "المرفوعات", "فاعل"], "3.1 p60")
    assert said.split(" (")[0] == "اسم ← المرفوعات ← فاعل"
