# Live check: the hosted site against answer keys

One folder per run date. It shows what is wrong now, so a later run can show what got fixed.

| File | What it is |
|---|---|
| `YYYY-MM-DD.html` | The report. Open it in a browser. |
| `YYYY-MM-DD-results.json` | Every word the site answered: what it said, what the key says. |
| `YYYY-MM-DD-verdicts.json` | Hand review of each Quran mismatch: engine / valid / corpus / context. |

Run again:

    SSL_CERT_FILE=/root/.ccr/ca-bundle.crt PYTHONPATH=. venv/bin/python backend/scripts/nahw/live_check.py docs/reports/live-check/NEW-results.json

Compare with the last run: a word that was wrong before and is right now is fixed.
Check that the fix is general: it should also fix words that are not in the old list.

## Runs

| Date | Words right (everyday / blind / hadith / Quran) | Biggest open item |
|---|---|---|
| 2026-10-29 | 33/33 · 578/588 · 298/303 · 920/969 | 23 typed ayahs miss their stored record (spelling) |
