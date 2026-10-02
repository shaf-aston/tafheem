"""The naming tree is data, so the walker is tested on tiny trees of its own."""
import pytest

from backend.services.syntax import walker


def leaf(branch, answer, role="حرف"):
    """`else` as the answer makes the one fall-through child."""
    pick = {"else": True} if answer == "else" else {"is": answer}
    return {"branch": branch, "book": "x", "role": role, **pick}


def root(*children):
    return {"branch": "root", "book": "x", "split": "kind", "children": list(children)}


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
        walker.validate(root({"branch": "a", "book": "x", "is": "harf"}))


def test_walk_reaches_leaf():
    tree = root(leaf("h", "harf"), leaf("f", "fil", "فعل"))
    assert walker.walk({"kind": "fil"}, tree) == ("فعل", ["root", "f"])


def test_walk_falls_to_else():
    tree = root(leaf("h", "harf"), leaf("rest", "else", "فعل"))
    assert walker.walk({"kind": "ism"}, tree) == ("فعل", ["root", "rest"])


def test_walk_no_match_is_none():
    assert walker.walk({"kind": "ism"}, root(leaf("h", "harf"))) is None
    assert walker.walk({"kind": "ism", "follows": "none"}) is None  # the rest of اسم is not filled in yet
