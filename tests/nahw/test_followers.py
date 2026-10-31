"""followers.chain_first: the first word of a chain of معطوفات, for any kind of word key."""
from backend.services.nahw.syntax.followers import FOLLOWERS, chain_first


def test_a_chain_climbs_to_its_first_word():
    # وَإِقَامِ الصَّلَاةِ وَإِيتَاءِ الزَّكَاةِ وَالْحَجِّ: each معطوف joined on the one before
    joined = {3: 2, 2: 1}
    assert chain_first(3, joined.get) == 1


def test_a_word_joined_on_nothing_is_its_own_first():
    assert chain_first(5, {}.get) == 5


def test_a_chain_that_loops_back_stops_instead_of_spinning():
    assert chain_first(1, {1: 2, 2: 1}.get) == 2
    assert chain_first(4, {4: 4}.get) == 4


def test_the_four_followers_are_named():
    assert set(FOLLOWERS) == {"معطوف", "توكيد", "بدل", "صفة"}
