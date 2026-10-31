"""#101/#102: real inputs to the hosted site, each word's answer against a key.
    SSL_CERT_FILE=/root/.ccr/ca-bundle.crt PYTHONPATH=. venv/bin/python backend/scripts/nahw/live_check.py OUT.json [every]
Sets: blind (never tuned on), hadith matn, everyday sentences, and Qur'an ayaat
(every Nth ayah) scored on case against the Quranic Corpus morphology and on role
against the Quranic Treebank where the site answered from its own rules."""
import json
import sys
import time

from backend.config import data_path
from backend.scripts.nahw.score_iraab import SETS, family, plain_role, post
from backend.scripts.nahw.score_quran import PAUSE, SAME_ROLE, UNSCORED_ROLES, case_key, corpus_index, sign_only
from backend.services.nahw import tarkeeb_store
from backend.services.quran import corpus as qc

API = "https://tafheem-app.vercel.app"
EVERYDAY = [
    ("أكرم محمد خالدا", ["فعل", "فاعل", "مفعول به"]),
    ("ضرب زيد عامرا", ["فعل", "فاعل", "مفعول به"]),
    ("قَالَ إِبْرَاهِيمُ لِأَبِيهِ آزَرَ", ["فعل", "فاعل", "مجرور", "بدل"]),
    ("شرب زيد الماء باردا", ["فعل", "فاعل", "مفعول به", "حال"]),
    ("جاء زيد راكبا", ["فعل", "فاعل", "حال"]),
    ("السَّمَاءُ صَافِيَةٌ", ["مبتدأ", "خبر"]),
    ("إِنَّ الْعِلْمَ نُورٌ", ["حرف توكيد ونصب", "اسم إن", "خبر إن"]),
    ("كَانَ الْجَوُّ جَمِيلًا", ["فعل ماض ناقص", "اسم كان", "خبر كان"]),
    ("ذَهَبَ الطُّلَّابُ إِلَى الْمَدْرَسَةِ", ["فعل", "فاعل", "حرف جر", "مجرور"]),
    ("لَمْ يَكْتُبْ زَيْدٌ الدَّرْسَ", ["حرف نفي وجزم وقلب", "فعل", "فاعل", "مفعول به"]),
]


def score_words(cards: list[dict], key: list[str]) -> list[dict]:
    aligned = len(cards) == len(key)
    out = []
    for i, want in enumerate(key):
        c = cards[i] if aligned else {}
        have = plain_role(c.get("role"))
        ok = have == plain_role(want) or bool(family(have)) and family(have) == family(plain_role(want))
        out.append({"word": c.get("word", ""), "want": want, "have": have, "case": c.get("case"), "ok": ok})
    return out


LOCAL = "--local" in sys.argv  # the engine here, the treebank record off: what the rules alone say


def ask(sentence: str) -> tuple[dict | None, int, str | None]:
    t = time.time()
    try:
        if LOCAL:
            from backend.services.nahw import iraab
            return iraab.analyze(sentence, recorded=False), round((time.time() - t) * 1000), None
        return post(API, sentence), round((time.time() - t) * 1000), None
    except Exception as e:  # noqa: BLE001 - a failed call is a result too
        return None, round((time.time() - t) * 1000), str(e)


def keyed(name: str, rows) -> list[dict]:
    out = []
    for ex in rows:
        ans, ms, err = ask(ex["sentence"])
        row = {"set": name, "id": ex.get("id"), "sentence": ex["sentence"], "ms": ms, "error": err}
        if ans:
            row |= {"source": ans["source"]["key"], "type": ans.get("summary"), "words": score_words(ans["words"], ex["key"])}
        out.append(row)
        print(name, ex.get("id"), err or sum(w["ok"] for w in row["words"]), "/", len(ex["key"]), ms, flush=True)
    return out


def quran(every: int) -> list[dict]:
    plain = json.loads(data_path("quran_imlaei_path").read_text(encoding="utf-8"))
    ayahs = [(s, a) for s in range(1, 115) for a, _ in qc.ayah_texts(s)][::every]
    out = []
    for s, a in ayahs:
        corpus_text = dict(qc.ayah_texts(s))[a]
        tags = qc.tags_for_ayah(s, a)
        typed = PAUSE.sub("", plain[f"{s}:{a}"]).split()
        index = corpus_index(typed, len(tags))
        record = tarkeeb_store.for_sentence(corpus_text)
        roles = [r["role"] for r in record["roles"]] if record and len(record["roles"]) == len(tags) else None
        ans, ms, err = ask(" ".join(typed))
        row = {"set": "quran", "id": f"{s}:{a}", "sentence": " ".join(typed), "ms": ms, "error": err, "words": []}
        if ans:
            row["source"] = ans["source"]["key"]
            cards = ans["words"]
            if index is None or len(cards) != len(typed):
                row["unaligned"] = True
            else:
                for card, at in zip(cards, index):
                    if at is None:
                        continue
                    want_case = case_key(tags[at])
                    if want_case in ("jarr", "nasb") and card.get("case") in ("jarr", "nasb") and sign_only(tags[at], card["word"]):
                        want_case = None
                    want_role = plain_role(roles[at]) if roles else ""
                    want_role = SAME_ROLE.get(want_role, want_role)
                    if want_role and (want_role.split()[0] in UNSCORED_ROLES or tags[at]["pos"] == "P" and family(want_role) != "harf"):
                        want_role = ""
                    have = plain_role(card.get("role"))
                    row["words"].append({
                        "word": card["word"], "corpus_case": want_case, "case": card.get("case"),
                        "case_ok": None if not want_case else card.get("case") == want_case,
                        "want": want_role, "have": have,
                        "ok": None if not want_role else have == want_role or bool(family(have)) and family(have) == family(want_role),
                        "pos": tags[at]["pos"], "features": tags[at]["features"]})
        out.append(row)
        print("quran", s, a, row.get("source"), err or "", ms, flush=True)
    return out


if __name__ == "__main__":
    every = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 40
    if LOCAL:
        json.dump(quran(every), open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
        sys.exit()
    rows = keyed("everyday", [{"id": f"e{i}", "sentence": s, "key": k} for i, (s, k) in enumerate(EVERYDAY, 1)])
    rows += keyed("blind", SETS["blind"]())
    rows += keyed("hadith", SETS["hadith"]())
    rows += quran(every)
    json.dump(rows, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
