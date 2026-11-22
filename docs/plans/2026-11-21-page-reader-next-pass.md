# Page reader: left for the next pass

From the code review of the page reader (Dictionary tab). The three important findings were fixed
(a timed-out read is not tried again, `read_queue_max=0` no longer refuses everything, tatweel is not
a letter). These six minor ones were left for the next pass; all are now done (2026-11-22).

- [x] **Orientation check on every unsure page.** Fixed: only below `read_sideways_confidence` (40; a sideways
      page reads near 25, a vowelled or photographed upright one 45-80). `tesseract.upright` (about a second) runs whenever
      the first read is unsure, even on an upright vowelled page. Run it only when the reading looks
      sideways (very low confidence, or few Arabic words), or skip it for screenshots.
- [x] **A paused line can ask before the shared pause ends.** Fixed with batch translation: the
      wait now loops until the shared gate is past.
- [x] **Two identical lines share the chosen word.** The chosen key is `${line.text}#${i}`, so a
      word chosen on one copy of a repeated line lights up on both. Key by line index too.
- [x] **Word spans ignore Space.** `PageWord` is `role=button` but only Enter looks up; Space should too.
- [x] **Confirming empty text says "No Arabic was found in this picture".** After the learner clears
      the box and presses Translate, the message should be about the box, not the picture.
- [x] **Stale health comment.** `backend/main.py` says the reader health is "tesseract + <model>";
      it is "tesseract + vision" (the model is never named).

Decisions already taken (2026-11-21), so these are not open questions:
Nahw gets text by select + copy · unsure pages wait for the learner · hover/first tap shows the word,
click/second tap looks it up · English-only pictures stay shaky and marked unsure · PDFs keep the
general "cannot open" card.
