"""Type a root into the live Sarf tab and check the table it gets back.

Unit tests fake the dictionaries; this asks the running server, real Lane and
Wiktionary behind it, so it catches a stale lane_verbs.json or an old deploy.
Each row is written out by hand from the book's paradigms, not from the code:
root -> the باب, "you (m)" in the past, "he" in the present.

    python3 deploy/sarf_check.py [base]     (default: the live Oracle server)
"""
import json
import sys
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://132-145-17-56.sslip.io"
EXPECT = {
    # أجوف: the root is typed, the dictionaries file the past (غَابَ).
    "غيب": ("I-daraba", "غِبْتَ", "يَغِيْبُ"),
    "قول": ("I-nasara", "قُلْتَ", "يَقُوْلُ"),
    "بيع": ("I-daraba", "بِعْتَ", "يَبِيْعُ"),
    "بوع": ("I-nasara", "بُعْتَ", "يَبُوْعُ"),
    "زيد": ("I-daraba", "زِدْتَ", "يَزِيْدُ"),
    "صوم": ("I-nasara", "صُمْتَ", "يَصُوْمُ"),
    "سير": ("I-daraba", "سِرْتَ", "يَسِيْرُ"),
    # سَمِعَ: the alif in both tenses hides a kasra, خَوِفَ يَخْوَفُ.
    "خوف": ("I-samia", "خِفْتَ", "يَخَافُ"),
    "نوم": ("I-samia", "نِمْتَ", "يَنَامُ"),
    "هيب": ("I-samia", "هِبْتَ", "يَهَابُ"),
    "نيل": ("I-samia", "نِلْتَ", "يَنَالُ"),
    # The past typed as the dictionaries spell it, and a sound verb.
    "غاب": ("I-daraba", "غِبْتَ", "يَغِيْبُ"),
    "كتب": ("I-nasara", "كَتَبْتَ", "يَكْتُبُ"),
}

failed = 0
for word, want in EXPECT.items():
    req = urllib.request.Request(f"{BASE}/api/morphology", json.dumps({"word": word}).encode(),
                                 {"content-type": "application/json"})
    got = json.load(urllib.request.urlopen(req, timeout=30))
    rows = {r["person"]: r["cells"] for r in (got.get("table") or {}).get("rows", [])}
    have = (got.get("form"), rows.get("you (m)", {}).get("madi"), rows.get("he", {}).get("mudari"))
    ok = have == want and got.get("table_note") is None
    failed += not ok
    print("ok  " if ok else "FAIL", word, *have, "" if ok else f"want {want} note {got.get('table_note')}")
sys.exit(f"{failed} failed" if failed else 0)
