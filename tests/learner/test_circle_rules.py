"""Who may open whose overview inside circles: the rule alone, no database."""
from backend.services.learner.circle_rules import can_see

KINDS = {"class": True, "family": False}


def test_an_admin_sees_a_member_of_a_circle_inside_theirs_but_not_a_sibling_circle():
    mine = {1: ("admin", "class")}
    assert can_see("sara", "omar", mine, {2: [2, 1]}, KINDS)          # circle 2 sits inside circle 1
    assert not can_see("sara", "omar", mine, {3: [3]}, KINDS)         # circle 3 is elsewhere


def test_a_fellow_member_sees_only_where_the_kind_shows_details():
    assert can_see("sara", "omar", {1: ("member", "class")}, {1: [1]}, KINDS)
    assert not can_see("sara", "omar", {1: ("member", "family")}, {1: [1]}, KINDS)


def test_nobody_else_is_visible_but_oneself_always_is():
    assert not can_see("sara", "omar", {}, {1: [1]}, KINDS)
    assert can_see("sara", "sara", {}, {}, KINDS)
