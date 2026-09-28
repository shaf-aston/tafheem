"""
Is this colloquial word in an independent reference?

The reference files are spelt with scholarly marks (ʔ ḥ ʕ ṣ ā), the units with
chat letters (2 7 3 aa). Both are folded to a consonant skeleton, so mar7aba and
marḥaba meet. That is loose on purpose: it answers "is this word there", never
"is it spelt right", and a word that is missing is a question for a native
speaker, not an error.

Every knob (the marks, prefixes, endings) and every reference (where it lives, its
licence, its file format) is in data/colloquial/reference/references.json. A new
reference is one entry there plus, for a new file format, one reader in READERS.
"""
import json
import re
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from functools import lru_cache

from backend.config import data_path

_TEI = "{http://www.tei-c.org/ns/1.0}"


@lru_cache(maxsize=1)
def config():
    folder = data_path("colloquial_dir") / "reference"
    return {**json.loads((folder / "references.json").read_text(encoding="utf8")), "folder": folder}


def skeleton(text):
    """Consonants only, one symbol per sound; vowels, doubling and silent marks dropped."""
    fold = config()["fold"]
    text = text.lower()
    for mark, plain in fold["marks"].items():
        text = text.replace(mark, plain)
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    for schwa in fold["schwas"]:
        text = text.replace(schwa, "a")
    text = re.sub(r"[^a-z0-9]", "", text)
    for pair, symbol in fold["digraphs"].items():
        text = text.replace(pair, symbol)
    text = re.sub(r"[aeiou]", "", text)
    for silent in fold["dropped"]:
        text = text.replace(silent, "")
    return re.sub(r"(.)\1+", r"\1", text)


def forms_of(word):
    """The skeletons a word may be found under once its prefixes and endings are tried."""
    fold = config()["fold"]
    plain = re.sub(r"[^a-z0-9]", "", word.lower())
    stems = {plain} | {plain[len(p):] for p in fold["prefixes"] if plain.startswith(p)}
    stems |= {s[:-len(e)] for s in set(stems) for e in fold["suffixes"] if s.endswith(e)}
    return {skeleton(s) for s in stems if len(s) > 1} - {""}


def _read_tei(path):
    """Every lemma and inflected form of a TEI dictionary, as skeletons."""
    return {skeleton(o.text or "") for o in ET.parse(path).getroot().iter(_TEI + "orth")} - {""}


READERS = {"tei": _read_tei}


@lru_cache(maxsize=None)
def known_forms(name):
    """The skeletons one reference holds; the file is downloaded on first use."""
    source = next(s for s in config()["sources"] if s["name"] == name)
    path = config()["folder"] / source["file"]
    if not path.exists():
        urllib.request.urlretrieve(source["url"], path)
    return frozenset(READERS[source["format"]](path))


def missing(words, names=None):
    """The words found in none of the chosen references (all of them by default)."""
    names = names or [s["name"] for s in config()["sources"]]
    known = set().union(*(known_forms(n) for n in names))
    floor = config()["fold"]["min_length"]
    return [w for w in words if (forms := forms_of(w)) and any(len(f) >= floor for f in forms) and not forms & known]
