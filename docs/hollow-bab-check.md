# Checking the hollow-root bab fix on the Oracle machine

Instructions for a Claude session that can reach the Oracle VM (the one with
`backend/data/lexicons.db` and `backend/data/arabic_dictionary.json`). The fix
was only tested against `lane_verbs.json`; the Wiktionary side and a Lane
rebuild were not. Report back what each step prints.

## 1. Get the branch

```bash
cd /home/ubuntu/tafheem            # wherever the repo lives on the VM
git fetch origin claude/zen-babbage-4c2iaa
git checkout claude/zen-babbage-4c2iaa
```

## 2. Run the tests

```bash
python -m pytest -q tests/test_verb_forms.py tests/test_bab_lookup.py \
  tests/test_lane_source.py tests/test_conjugation.py tests/test_ilal.py
```

## 3. Ask both real sources about hollow roots

```bash
python - <<'EOF'
from backend.services import verb_forms
for root in ["غيب", "قول", "بيع", "بوع", "خوف", "نوم", "طول", "زيد", "صوم", "سير", "هيب", "نيل"]:
    v = verb_forms.babs_of(root)
    print(root, v["form_key"], [(r["label"], r["source_keys"]) for r in v["readings"]])
EOF
```

What to look for:
- Every root prints a `form_key`. Any that prints `None` still has no table.
- `خوف`, `نوم` and `هيب` should come out as `I-samia` (سَمِعَ, خَافَ يَخَافُ).
  Lane's list has none of them, so only Wiktionary can supply them; if they
  are `None`, the next step is the fix.
- و roots never land on `I-daraba`, ي roots never on `I-nasara`.

## 4. If the سَمِعَ-type hollow verbs are missing

Rebuild Lane's list and see whether خَافَ appears:

```bash
python -m backend.scripts.build_lane_verbs /tmp/lane_verbs.json
python -c "import json; d=json.load(open('/tmp/lane_verbs.json')); print(d.get('خاف'), d.get('نام'))"
```

`build_lane_verbs.bab_vowel()` reads the alif in خَافَ as a fatha, so a
سَمِعَ verb would be misread as `a~a` and dropped. If that is what happens,
the fix belongs in `bab_vowel()`/`verbs_of()` in the build script (read the
past vowel from Lane's hollow past spelling, e.g. خَوِفَ), not in
`verb_forms.py`. Keep `lane_verbs.json` built only by the script.

## 5. Check the app end to end

```bash
curl -s localhost:8000/api/morphology -H 'content-type: application/json' \
  -d '{"word":"غيب"}' | python -m json.tool | grep -E '"form"|form_key|table_note'
```

`form` should be `I-daraba` and `table_note` should be `null`.
