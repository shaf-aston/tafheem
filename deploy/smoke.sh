#!/bin/bash
# Times one real request per tab against a live site. Run: bash deploy/smoke.sh [base-url]
BASE="${1:-https://132-145-17-56.sslip.io}"
Q=$(printf 'كتب' | od -An -tx1 | tr ' ' % | tr -d '\n')   # url-encoded root
S=$(printf 'رحمة' | od -An -tx1 | tr ' ' % | tr -d '\n')
fails=0
hit() {  # label method path [json-body]
  local out
  if [ -n "${4:-}" ]; then
    out=$(printf '%s' "$4" | curl -s -o /dev/null -m 60 -w '%{http_code} %{time_total}' -X "$2" -H 'content-type: application/json' --data-binary @- "$BASE$3")
  else
    out=$(curl -s -o /dev/null -m 60 -w '%{http_code} %{time_total}' "$BASE$3")
  fi
  printf '%-14s %s s\n' "$1" "$out"
  [ "${out%% *}" = 200 ] || fails=$((fails+1))
}
hit health      GET  /api/health
hit sources     GET  /api/sources
hit analyse     POST /api/analyze '{"sentence":"ذهب الطالب إلى المدرسة"}'
hit examples    GET  /api/tarkeeb/examples
hit quran-ayah  GET  /api/quran/1/2
hit quran-surah GET  /api/quran/surah/1
hit tarkeeb     GET  /api/quran/1/2/tarkeeb
hit quran-find  GET  "/api/quran/search?q=$S"
hit editions    GET  /api/quran/editions
hit dictionary  GET  "/api/dictionary/search?q=$Q"
hit root        GET  "/api/dictionary/root-meaning?root=$Q"
hit lexicons    GET  "/api/dictionary/lexicons?root=$Q"
hit daleel-book GET  /api/daleel/books
hit daleel      GET  "/api/daleel?q=$S"
hit tamreen     GET  /api/tamreen
hit timelines   GET  /api/timelines
hit practice    POST /api/practice '{"sentence":"ذهب الطالب"}'
hit notes       GET  /api/notes
echo "failures: $fails"
exit $fails
