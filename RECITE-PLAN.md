# Reciting aloud in the Memorise tab

You open a page, recite it, and the app follows you: it marks the words as you
go and tells you where you went wrong. Design approved 2026-09-05.

Prototype of the agreed screen: https://claude.ai/code/artifact/c4c7017d-409c-4151-a886-a230d6cdb508
Earlier comparison of the three shapes: https://claude.ai/code/artifact/56732943-f874-4508-ae93-977587efa9cf

## Standing rules, decided and not to be re-opened

1. **Fold first, compare second.** مَٰلِكِ and مالك are the same word: the small
   standing alef is a full alef. `recitedForms` in `frontend/src/lib/arabicText.js`
   already returns both spellings. Every comparison added by this feature runs
   *after* that folding. A rule that fires on a difference in writing is a bug,
   not a near-miss. Same for ٱ against ا, ى against ي, and the tatweel.
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
5. **Its own key.** `RECITATION_GROQ_API_KEY` in `.env`, separate from
   `GROQ_API_KEY`, so an hour of reciting cannot spend the allowance the grammar
   answers run on.
6. **20 requests a minute is the ceiling**, not the hours. Groq's free allowance
   is 20 req/min, 7,200 audio-seconds/hour, 28,800/day. A chunk every 3 seconds
   sits exactly on the limit; every 4 seconds does not. That number is config.

## Milestones

Each one is finished when its "done when" is true, and nothing later starts until
it is. Every pure module gets its runnable check in the same milestone.

### M0. Can this machine keep up on its own? Done 2026-09-05.
**Yes, but not on the settings it uses today.** Speed was never the problem.
Hearing all of what was said is.

Measured on real recitation (Alafasy, al-Fatihah then 2:255-257 from
everyayah.com), joined, cut to length and re-encoded as webm opus, which is what
a browser sends. Model warmed first, so loading it (about 6 seconds) is paid once
at startup and is not in any number below. "Came back" is how much of the real
ayah text returned, in order, folded by rule 1 so a spelling variant is not
counted as a miss.

One whole recording at a time:

| ear and settings | 10s | 30s | 60s |
|---|---|---|---|
| **today's** dictation knobs: base, no timestamps | 100% in 1.4s | **24%** in 1.0s | **31%** in 2.1s |
| base, timestamps back on | 100% in 0.9s | 76% in 2.3s | 69% in 2.4s |
| base, timestamps on, no silence trim | 100% | 76% in 4.0s | 66% in 3.1s |
| base, timestamps on, beam 5 | 100% | 76% in 3.3s | 62% in 3.3s |
| **small, timestamps on** | 100% in 3.0s | **100%** in 6.4s | **97%** in 7.4s |
| Groq, for comparison | 100% in 1.6s | 100% in 0.3s | 100% in 0.4s |

Three things that decide the design:

1. **`without_timestamps=True` is why a long recitation comes back in pieces.**
   It is right for one short ayah, where it halved the wait, and it silently
   throws away three quarters of thirty seconds. Following needs its own
   settings; the dictation path keeps the ones it has.
2. **A near-silent piece makes the local engine spin.** Reading 4 second pieces
   one after another, two of the fifteen took 6.4s and 16.7s and returned
   nothing at all, while every piece with speech in it took about 0.9s. Silence
   must be refused before it is read, never sent and waited on.
3. **Cut on a clock and you cut words in half.** 4 second pieces returned
   إيا كان عبوا for إياك نعبد. A window that overlaps the one before it fixes
   this.

Reading in a moving window, which is what following actually does:

| ear | window | slowest read | of it came back |
|---|---|---|---|
| base | 4s pieces, no overlap | 13.3s (a silent one) | 52% |
| base | 8s window every 6s | 1.6s | 76% |
| **base** | **10s window every 8s** | **1.1s** | **86%** |
| small | 8s window every 6s | 2.9s | 76% |
| **small** | **10s window every 8s** | **2.9s** | **97%** |
| **Groq** | **10s window every 4s** | **0.3s** | **93%** |

**The verdict.** Both ears keep up, so the ladder in M3 is real and the local ear
is a floor that never runs out, not a pretence. Ten seconds of sound read every
eight seconds, on `small` with timestamps on, returns 97% of a recitation and
takes 2.9 seconds of a machine that has 8 to spare. Groq returns 93% and answers
in a third of a second, so with it the window can move every 4 seconds, which is
rule 6's ceiling and not a limit of the machine.

What that costs the reader: a word is marked between 3 and 11 seconds after it is
said on this machine, or between 4 and 5 with Groq. Marks arrive a window at a
time, not word by word, which suits rule 3 rather than fighting it: nothing is
allowed to mark until later words are in, and now they arrive together anyway.

Settings this hands to M4, all of them config and none of them in code:
`recitation_follow_model` small, `recitation_follow_window_s` 10,
`recitation_follow_step_s` 8 on this machine and 4 on Groq, and a level gate
before anything is sent, reusing `voice-level` in `dictation.json`.

### M1. The orange rule. Done 2026-09-05.
`frontend/src/lib/soundalike.js`, pure, one exported question: are these two
*different* words that a microphone confuses? The order is enforced inside it
rather than asked of every caller, so مَٰلِكِ against مالك answers false because
`sameSpokenWord` answers true first. Groups and knobs in
`frontend/src/recite.json`, drawn wider than a phonetics book would draw them
because being wrong here shows orange, and being wrong the other way calls a
reciter mistaken when they were not.

Added after seeing real output, not designed in: a lost ال counts as a near miss.
Groq really did return رحمن for ٱلرَّحْمَٰنِ where a window ended. Only when three
letters are left without it, so ٱللَّهِ against لله stays a mistake.
17 tests in `soundalike.test.js`.

### M2. The follower. Done 2026-09-05.
`frontend/src/lib/follow.js`, pure, the deep module. In: the words of the page,
the words heard so far, where reciting began, and whether it has stopped. Out:
where the reciter is, one state for every word, and the words said that are not
in the book.

It lines the whole thing up at once and takes the cheapest reading, rather than
walking a pointer forward, because a pointer cannot tell a wrong word from an
added one until it sees what follows: وَمَا said in place of وَلَا looks exactly
like وَمَا added in front of it. What each mistake costs is in `recite.json`, and
those costs are the rules of rule 2 written as numbers.

Two things settled by the tests failing rather than by argument:
- **An added word costs more than a wrong one** (5 against 4). Cheaper, and the
  last word of an ayah said wrongly was reported as a word added and a word never
  reached, which is two accusations for one slip.
- **A stray word with nothing after it is read as the next word said wrongly.**
  Nothing separates the two readings while it is the last thing heard, so the
  gentler is taken, and it corrects itself the moment the reciter carries on.

Nothing is carried between calls: the same words in always give the same answer
out, which is what lets a mark disappear when the next window hears the word
properly. `joinWindows` is here too, because taking the overlap of two windows as
one is the same "is this the same word" question and must not be answered twice.
25 tests in `follow.test.js`, covering a clean run, a skip, a skipped first word,
a page opened halfway down, an addition, a repeated phrase, a transcript that
changes its mind, and the settle lag on each kind of mark.

**Checked against real output, not only against typed strings.** The M0
recordings were put through it: on Groq's reading of a correct recitation, 27 of
29 words came back right, one mark was the audio running past the page, and one
was نَسْتَعِينُ heard as نستقبل, a plain mistake that is nobody's slip. So even at
its best about one word in thirty will be marked wrongly, which is what the
orange state and the settle lag exist for, and is worth saying on screen rather
than hiding.

### M3. Two ears in a list
**Its own key: done 2026-09-05.** `RECITATION_GROQ_API_KEY` in `.env`,
`recitation_groq_api_key` in `backend/config.py`, and one property,
`listening_key`, is the only place the choice between the two keys is made. It
falls back to the shared key when no separate one is set, so a machine that never
had one listens exactly as before. `hosted.py` spends it; `services/ai/` still
spends `GROQ_API_KEY` and the two no longer touch. Three tests pin it.

The rest:
`backend/services/recitation/`. The one `if` in `transcribe` becomes an ordered
list of ears. Each ear says whether it is available, and an ear that hits its
limit steps aside quietly so the next answers. Ear one is Groq on the new key,
ear two is this machine. Chrome's built-in recognition was considered and
rejected: it ships audio to Google and nobody publishes that it supports Arabic.
**Done when:** pulling the key makes it fall through to local with no error on
screen, and a test proves the order.

### M4. A moving window
The browser posts audio while still recording, instead of once at the end. Not
pieces cut on a clock: a window of the last `follow-window-s` seconds, sent every
`follow-step-s`, so the same word is heard twice rather than cut in half. M0
measured 10 and 8 on this machine, 10 and 4 on Groq, and both are config.
Silence is never sent: the level meter already in `ui/MicButton.jsx` gates it,
because a silent window costs the local engine up to 17 seconds and returns
nothing. That file stays the one that knows how a browser records; the new
behaviour sits beside it, not inside it.
Done 2026-09-05, in `frontend/src/lib/useReciting.js`, and not the way this
milestone was written. It sends **the whole recording so far**, not the last few
seconds, because a recording is only whole from its beginning and a slice out of
the middle is something no engine can read. What comes back each time is
therefore the whole thing read again with more of the sentence behind it, which
is what lets a mark correct itself. Every `window-s` a fresh recording starts and
what was heard is kept in front of it, so an hour is many short recordings.

Watched in the running app: three requests went out at 17:35:12, 17:35:16 and
17:35:16, answered by Groq on the listening key.

### M5. Marks on the page. Done 2026-09-05.
Third choice in "How you answer": Type it, Pick from 4, **Recite it**. What is
taken out is chosen beside it, as two buttons rather than the typist's five:
"Show all" for reading along, "Hidden" for saying it from memory (M7).
`MemorisePanel.jsx` holds no rules; every state on the page came from
`follow.js`, and `lib/reciteColors.js` is the one place a state meets a colour so
the word and the pill beside it can never disagree.

### M6. The strip. Done 2026-09-05.
`components/ReciteStrip.jsx`, sticky at the foot of the page: the microphone, what
it is hearing, the tally, and one pill an ayah.

### What clicking through found that the tests did not
Both of these were green in 536 tests and wrong on the screen.

1. **A silent room was marked as twelve mistakes.** Music was playing, the engine
   returned موسيقى, those words were lined up against the page, and somebody who
   had not opened their mouth was shown twelve red words. A loudness gate would
   not have saved it, because there really was sound: measured in the room, the
   level averaged 0.30 against a voice threshold of 0.04. The fix is a rule, not
   a threshold: `anchor-words` in `recite.json`. Nothing on the page is marked at
   all until two of its words have actually been heard, and until then the strip
   says "Listening. Start from the top of the page."
2. **Stop did not stop.** One press left the microphone recording and sending;
   it took three. The release waited on the last reading coming back. Now the
   microphone is let go the moment the button is pressed and the last reading is
   sent without anything waiting on it. Checked in the log: last request 17:42:19,
   stop pressed 17:42:24, nothing after it.

### Reciting the page without a person: the fake microphone
Handing the last check to the reader was the wrong answer. A microphone is a
stream of sound, and a recording of al-Fatihah played into one is a stream of
sound, so the browser can be given the recitation as its microphone and the whole
thing driven start to finish with nobody in the room. The rig is seven mp3s and
twenty lines that hand `getUserMedia` a stream fed from them; it lives in the
scratchpad, never in the repo, and is put in place for a run and taken away after.

Three more defects it found, all green in the tests and wrong on the screen:

3. **Two words of al-Fatihah lost for good.** رَبِّ ٱلْعَٰلَمِينَ came back marked
   as never said, though the reading for that window held them. When a window
   ended while a reading was still on its way, the last full reading was dropped
   and the window was folded away holding a reading that stopped short, and
   nothing later can put back a word that is no longer in what was heard. Now the
   fold waits for the reading on its way and then asks for the last one.
4. **The engine's full stops were being read as part of the word.** "الضال."
   against ٱلضَّآلِّينَ. `wordsHeard` now keeps Arabic and drops everything else.
5. **Sound after the reciter finished was put on the page.** The last window held
   only the room, the engine wrote موسيقى, and it was reported as a word added to
   al-Fatihah. A reading with not one word of the page in it is now left out.

One reading a window was also being paid for twice, seen as the same byte count
sent twice in the log; a window now only sends sound it has not sent before.

**Where it stands after the fixes**, same recording, same page, at "1 in 3":
28 of 29 words right, nothing lost, nothing added, every covered word revealed by
being recited. The one mistake is real: نَعْبُدُ came back as اعبد and is marked
red. A word one letter away from the printed one is arguably doubt rather than an
accusation, but the orange rule is about letters that sound alike, and widening it
is a decision, not a fix.

Still unchecked, and only a person can: a human's own voice, in a real room, on a
real microphone.

### M6a. Still to do on the strip
A pill is a label today, not a button. Tapping one should open that ayah and take
the page to it.

### M7. Hidden words and reciting together. Done 2026-09-05.
Reciting off a page you can read is not a test of remembering it, so "How much is
missing" applies while reciting too. A hidden word is a plain line the width of
the longest hidden word on its line, so its own length gives nothing away, and the
only thing that uncovers it is saying it. "None" is the read-along; anything else
is the test.
**Checked:** at "1 in 3", eight covered words on al-Fatihah, all eight uncovered by
the recitation played into the microphone.

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
microphone, before any of this is called done.

## Not doing

- No paid provider, no card, ever.
- No second copy of the Qur'an: the page comes from `lib/books.js` as it already does.
- No guessing which ayah you are on. The page is open, so this is lining up
  against known words, not searching all 6,236.
