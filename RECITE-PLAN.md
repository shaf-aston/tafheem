# Reciting aloud in the Memorise tab

You open a page, recite it, and the app follows you: it marks the words as you
go and tells you where you went wrong. Design approved 2026-09-05. How it works
today: `CORE-FLOW.md` step 5 and `docs/core-flow-detail.md` (Reciting detail).
How it was built: git history.

## Standing rules, decided and not to be re-opened

1. **Fold first, compare second.** مَٰلِكِ and مالك are the same word: the small
   standing alef is a full alef. `recitedForms` in `frontend/src/lib/text/arabicText.js`
   returns both spellings. Every comparison runs *after* that folding. A rule that
   fires on a difference in writing is a bug, not a near-miss. Same for ٱ against ا,
   ى against ي, and the tatweel.
2. **Five states, and their colours.**
   - said and right: fades to `--text-dim`, never lit up
   - **orange** `--warn`: two genuinely different words that sound nearly the
     same, ص heard as س, ض heard as ظ. Means "I cannot tell whether you slipped
     or I mis-heard", never "you are wrong"
   - **red** `--danger`: a different word
   - **red outline**: a word in the book never said
   - **red dashed**: a word said that is not in the book. Counts as wrong.
3. **Nothing marks instantly.** A word holds plain until `settle-words` more have
   gone past it, because the machine revises what it heard as it hears more.
4. **What was heard sits on the line beside the word**, not under it.
5. **Its own keys.** `LISTENING_GROQ_API_KEYS` in `.env` (`listening_groq_api_keys`
   in `backend/config.py`, a comma list), separate from `GROQ_API_KEY`, so an hour
   of reciting cannot spend the allowance the grammar answers run on. The property
   `listening_keys` is the only place the choice is made; with no own key it falls
   back to the shared one. `services/ai/` never touches the listening keys.
6. **Groq's per-minute allowance is the ceiling**, not the hours. The pacing
   numbers (`step-s`, `asks-per-minute`, `window-s`, `pause-s`) are config in
   `frontend/src/config/recite.json`; read the values and the reasons there, never copy
   them here.
7. **Silence is never sent.** `voice-level` in `frontend/src/config/dictation.json`
   gates it: a silent window costs the local engine many seconds and returns
   nothing.
8. **Nothing is marked until the reciter is on the page.** `anchor-words` in
   `recite.json`: room noise the engine writes down as words must not be shown as
   mistakes.
9. **A recording is cut at a pause or at `window-s`, never on a short clock.** A
   clock cut lands mid-word and the word is lost from both pieces.

## Open milestones

Each is finished when its "done when" is true. Every pure module gets its
runnable check in the same milestone.

### M6a. Still to do on the strip
A pill in `components/memorise/ReciteStrip.jsx` is a label, not a button.
Tapping one should open that ayah and take the page to it.

### M8. How long you recite for
An ayah at a time by default: the microphone lets go at the pause and takes
itself up again. "Keep going" runs until stopped, for hours, on whichever ear is
still answering.
**Done when:** both run, and the strip says which ear answered.

### M9. Kept score
Answers filed in `progress.db` under their own module, the way the quiz already
does. A recitation is not a quiz answer and does not share its module name.
**Done when:** a session shows up in the insights panel.

### M10. Clicked through
`npm run probe` against the running page, and a real recitation into a real
microphone (a human voice, in a real room), before any of this is called done.

### Open decision
A word one letter away from the printed one (نَعْبُدُ heard as اعبد) is marked
red. It is arguably doubt rather than an accusation, but the orange rule is about
letters that sound alike, so widening it is a decision, not a fix.

## Not doing

- No paid provider, no card, ever.
- No second copy of the Qur'an: the page comes from `lib/memorise/books.js` as it already does.
- No guessing which ayah you are on. The page is open, so this is lining up
  against known words, not searching all 6,236.
