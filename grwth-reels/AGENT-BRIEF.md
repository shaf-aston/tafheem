# Brief: making GRWTH Instagram reels from Frame.io footage

Read this whole file before doing anything. Follow it step by step. Do not skip steps, do not invent your own style, do not "improve" the look. When this file does not answer something, ask the user.

---

## 0. What you are making, in one paragraph

Short vertical videos (Instagram Reels, 15 to 25 seconds) for GRWTH, a UK company that does sales training, done-for-you sales growth and sales careers. Each reel is one coach (usually Shayan Hashmi) making ONE clear point about sales, filmed at events. The user has already approved one reel ("POV: you went to an EVENT to get value & ended up giving it"). Every new reel must look exactly like that one. Only the footage, the hook words and the captions change.

You get three files from the user:
1. `AGENT-BRIEF.md` (this file)
2. `reel.py` (the builder; it does all the editing for you)
3. `pov-final.mp4` (the approved example; open it and study it before starting)

---

## 1. Rules (break none of these)

1. **Never delete, rename, move or overwrite anything in Frame.io.** You only download originals and upload new files into one folder you create: `Reels - finished`.
2. **Never post anything publicly** (Instagram, TikTok, YouTube, anywhere). The user posts.
3. **Free tools only.** ffmpeg, Python, Pillow, faster-whisper. No paid APIs, no paid apps, no sign-ups.
4. **No Skool material.** If you see anything from Skool (course videos, lessons), do not open, download or use it.
5. **Never guess who someone is.** Only call someone "Shayan" if he matches the description in section 2. If unsure, ask.
6. **Never invent claims.** Hooks and captions say only what is said in the clip. No income figures, no "guaranteed", no "#1", unless he literally says it.
7. **Writing style:** short, plain words. Never use the long "em dash" character. Use commas or full stops.
8. **One reel at a time.** Finish, check and deliver reel 1 before starting reel 2.
9. **For the first reel, show your plan (step 5) to the user and wait for a yes before building.** After the user has approved two plans, you may build without asking.

---

## 2. The people

| Name | Role | How to recognise |
|---|---|---|
| Shayan Hashmi | Coach, main face of the reels | Long black beard, black GRWTH cap, often a lanyard, talks straight to camera at events |
| Imran Farooq | Coach | Ask the user before using |
| Zeshan Haroon | Coach | Ask the user before using |

People in the background are not named. Never put a name on screen.

Audience: people who want to sell better or start a career in sales. They scroll fast. They stop for a bold statement, a surprise, or a "that's me" moment.

---

## 3. Set up your machine (once)

Run these and make sure each one works:

```bash
ffmpeg -version          # must print a version
python3 -c "import PIL; print('pillow ok')"
pip install faster-whisper pillow
python3 -c "import faster_whisper; print('whisper ok')"
```

**Fonts.** The look needs two fonts: a very heavy one ("black") and a bold one.
- On Windows: `C:/Windows/Fonts/ariblk.ttf` (Arial Black) and `C:/Windows/Fonts/arialbd.ttf` (Arial Bold).
- On Linux/Mac: install the free Microsoft core fonts (`sudo apt-get install ttf-mscorefonts-installer`, then find them with `fc-list | grep -i arial`). If that is impossible, download the free Google font **Archivo Black** for "black" and **Inter Bold** for "regular_bold", and tell the user you used them.

Put the font paths in the `fonts` section of each reel's config (section 6).

**Logo.** Ask the user for `grwth-logo.png` (white GRWTH logo on transparent background). Without it you cannot make the end card. Do not draw your own logo.

---

## 4. Find the footage (Frame.io)

1. List all projects and folders. Write a simple list for yourself: file name, length, what it shows (look at 3 or 4 frames of each clip).
2. Sort clips into two piles:
   - **Talking clips:** Shayan talking to camera, clear voice, his face visible, one point said in 5 to 20 seconds.
   - **B-roll:** clips with no one talking to camera: the event room, people at tables, the stage, crowds, handshakes. Same event as the talking clip if possible.
3. Pick a talking clip where he says one complete idea. Good signs: he starts with a statement ("So now you're in control"), he ends a thought cleanly ("That's how you get people to open up"). Bad signs: he trails off, someone interrupts, loud music over him, his face is cut off.
4. **Download the original file**, not the preview/proxy. Originals are usually the biggest file. Keep the original name.
5. Put each reel in its own folder, for example `reels/2026-11-20-ask-questions/`, with the clips inside.

To get the exact start and end second of a moment, play it and note the times, or transcribe the whole clip first (see step 6) and read the word times.

---

## 5. Plan the reel (write this down before building)

Fill in this table and show it to the user (for the first reels):

```
Reel: <short name>
Point he makes (one sentence): <e.g. Asking questions puts you in control of a sales conversation>
Hook (on screen, first 6 s): <lines, see rules below>
Clip A (opening shot, under the hook): <file, from s to s>   why: <e.g. wide shot of the event hall>
Clip B (him talking): <file, from s to s>
Cutaways: <b-roll file, from s, for how long, placed over which words>
Key words (big pop-up words): <3 to 6 words>, ice-blue one: <1 word>
Total length: <15 to 25 s>
Caption for Instagram: <1 to 2 lines>
```

### Hook rules
- The hook is the most important part. It is on screen from the very first frame.
- 5 to 8 lines, building one line at a time over about 4 seconds, then it stays until about second 6.
- Mix small lines (connecting words) and big lines (the strong words). Pattern that works: small, small, BIG, small, BIG, small, BIG.
- Exactly ONE big line in ice blue: the payoff or twist (in the example: "giving it").
- Formats that work: `POV: ...`, a bold claim (`Most reps talk too much`), a twist (`I went to learn & ended up teaching`).
- Every hook must be true to what happens in the clip.

Approved example:
```
POV:              small   at 0.2 s
you went to an    small   at 0.2 s
EVENT             BIG     at 0.7 s
to get            small   at 1.3 s
value             BIG     at 1.7 s
& ended up        small   at 3.0 s
giving it         BIG ice at 3.6 s
```

### Opening shot (clip A) rules
- 4 to 6 seconds of something that fits the hook, usually a wide shot of the event or him arriving, with little talking (it plays at half volume under the hook).
- Then cut straight to him talking (clip B).

### Zoom rules
- Split clip B into pieces at the START of each new sentence (use the word times).
- Alternate the pieces: normal (zoom 1.0), punched in (zoom 1.14), normal, punched in...
- Never cut in the middle of a word. Cut exactly at the start time of the first word of a sentence.

### Cutaway rules
- 1 to 1.3 seconds each, about one every 4 to 5 seconds of talking, 2 to 3 per reel.
- Place them over less important words (e.g. "going to start"), never over a key word and never over the last sentence.
- His voice keeps playing underneath. Only the picture changes.

### Key word rules
- 3 to 6 words per reel, the strongest word of each sentence (in the example: control, authority, questions, relaxed, everything).
- They appear bigger, alone, exactly when he says them.
- One of them in ice blue: the most important idea of the reel (in the example: authority).

---

## 6. Build the reel with `reel.py`

The builder works in three commands. Run all of them from inside the reel's folder, with `reel.py` next to it or referenced by its path.

### 6.1 Write `reel.json`

Copy this example (it is the config of the approved reel) and change the values. Times in `segments` are seconds inside each source file. All other times (`hook`, `captions_from`, `cutaways.at`) are seconds in the FINISHED reel.

```json
{
 "out": "2026-11-20-ask-questions.mp4",
 "fonts": {"black": "C:/Windows/Fonts/ariblk.ttf", "regular_bold": "C:/Windows/Fonts/arialbd.ttf"},
 "segments": [
  {"src": "event-hall.mp4", "in": 0,    "out": 6,    "zoom": 1.0,  "y": 0.35, "volume": 0.5},
  {"src": "shayan-talk.mp4", "in": 0,    "out": 1.88, "zoom": 1.0,  "y": 0.21},
  {"src": "shayan-talk.mp4", "in": 1.88, "out": 4.24, "zoom": 1.14, "y": 0.3},
  {"src": "shayan-talk.mp4", "in": 4.24, "out": 7.12, "zoom": 1.0,  "y": 0.21},
  {"src": "shayan-talk.mp4", "in": 7.12, "out": 9.86, "zoom": 1.14, "y": 0.3},
  {"src": "shayan-talk.mp4", "in": 9.86, "out": 11.43,"zoom": 1.0,  "y": 0.21}
 ],
 "hook": {"until": 6.0, "lines": [
  {"text": "POV:",           "size": "small", "at": 0.2},
  {"text": "you went to an", "size": "small", "at": 0.2},
  {"text": "EVENT",          "size": "big",   "at": 0.7},
  {"text": "to get",         "size": "small", "at": 1.3},
  {"text": "value",          "size": "big",   "at": 1.7},
  {"text": "& ended up",     "size": "small", "at": 3.0},
  {"text": "giving it",      "size": "big", "ice": true, "at": 3.6}
 ]},
 "captions_from": 5.8,
 "keys": {"control": "white", "authority": "ice", "questions": "white", "relaxed": "white", "everything": "white"},
 "cutaways": [
  {"src": "broll-tables.mp4", "at": 10.24, "len": 1.26, "from": 4.0},
  {"src": "broll-tables.mp4", "at": 14.64, "len": 0.96, "from": 12.0}
 ],
 "end_card": {"logo": "grwth-logo.png", "text": "Follow for more"}
}
```

What each field means:

| Field | Meaning | How to choose it |
|---|---|---|
| `out` | Finished file name | `YYYY-MM-DD-short-name.mp4` |
| `segments` | The pieces of footage, in order | First: opening shot (`volume` 0.5). Then the talking clip cut at sentence starts. |
| `in` / `out` | Start and end second inside that source file | From word times (step 6.3) or by playing the clip |
| `zoom` | 1.0 normal, 1.14 punched in | Alternate 1.0 / 1.14 per sentence |
| `y` | Which part of the frame to keep when cropping: 0 = top, 0.5 = middle, 1 = bottom | Pick so his whole face (cap to chin) is inside. Check on the contact sheet. Usually 0.2 to 0.35 for vertical phone footage. |
| `volume` | 1.0 normal, 0.5 half | 0.5 for the opening shot, leave out for him talking |
| `hook.lines[].at` | Second the line appears | First lines at 0.2, then 0.4 to 1.2 s apart |
| `hook.until` | Second the hook disappears | Same second clip B starts (usually 6.0) |
| `captions_from` | Captions start here | 0.2 s before his first word in clip B (look in words.json) |
| `keys` | Big pop-up words, `"white"` or `"ice"` | One `"ice"` only. Write the word without full stops. |
| `cutaways[].at` | Second in the finished reel the b-roll starts | Over a weak phrase, see cutaway rules |
| `cutaways[].len` | How long it shows | 0.9 to 1.3 |
| `cutaways[].from` | Second inside the b-roll file to start from | A moment with movement and no one looking at the camera |

### 6.2 Cut

```bash
python reel.py cut reel.json
```
Makes `band.mp4` (all pieces joined, cropped, zoomed). It prints the length. If it errors with "Stream specifier ':a' matches no streams", one clip has no sound: tell the user, pick another clip.

### 6.3 Words (timings for captions)

```bash
python reel.py words reel.json
```
Makes `words.json` with every word and its start/end second, and prints the sentence.

**Then read the printed sentence and compare with what he actually says.** Whisper makes mistakes (in the test it heard "He can" instead of "You can", and "You're the position" instead of "You're in the position"). Open `words.json` and fix the spelling of wrong words by hand. Keep the times as they are. Example fix:
```json
{"w": "He", "s": 11.2, "e": 11.4}   ->   {"w": "You", "s": 11.2, "e": 11.4}
```
If a word is missing, add it between its neighbours with a guessed time inside the gap.

Now use the word times to set the zoom cut points (6.1 `segments`) and `captions_from`, then run `cut` and `words` again if you changed segments.

### 6.4 Render

```bash
python reel.py render reel.json
```
Makes the finished reel and `sheet.jpg` (a grid of frames, 2 per second). It also prints the caption groups, like `now you're | in | control. | ...`. Read them: every word he says after the hook must be there, in order.

---

## 7. Check the reel (every time, no exceptions)

Open `sheet.jpg` and look at EVERY frame. Then watch the video once with sound. Tick every line:

**Picture**
- [ ] The very first frame shows hook text (not black, not a logo).
- [ ] Hook builds line by line, right-aligned, top of the video area, one ice-blue line.
- [ ] His face (cap to chin) is fully inside the frame in every talking shot. If not, change `y` for that segment.
- [ ] No caption or key word covers his eyes or mouth. If it does, the shot is too zoomed or the `y` is wrong.
- [ ] Every caption is readable (white with black outline).
- [ ] Key words pop up big exactly on the word, one in ice blue.
- [ ] Zooms change at the start of sentences, not mid-word.
- [ ] Cutaways are 1 s or so, not over key words, not black, not frozen.
- [ ] No black or frozen frames anywhere except the end card.
- [ ] Ends on the black end card with the GRWTH logo and "Follow for more".

**Sound**
- [ ] His voice is clear the whole time, no cuts mid-word, no clicks at cuts.
- [ ] Voice fades out gently right before the end card (no hard stop).
- [ ] Loudness: run
  ```bash
  ffmpeg -hide_banner -i <out>.mp4 -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|Peak):"
  ```
  `I` must be between -15 and -13 LUFS. `Peak` must be -1.5 dBFS or lower (e.g. -1.6 is fine, -1.2 is not).

**Content**
- [ ] The hook is true to what he says.
- [ ] Captions spelled correctly, match his words.
- [ ] Length 15 to 25 s (end card included).
- [ ] File is 1080x1920, 30 fps. Check with `ffprobe -v error -show_entries stream=width,height,r_frame_rate -of csv <out>.mp4`.

If any box fails: fix the config or words.json, render again, check everything again. Only deliver when all boxes pass.

### Common problems and fixes

| Problem | Fix |
|---|---|
| First caption word missing | `captions_from` is too late. Set it 0.2 s before his first word. |
| Caption on screen too long or overlapping | Check `words.json` times; a word may have a wrong end time. |
| Face cut off | Change that segment's `y` (lower number shows more of the top). |
| Too blurry when zoomed | Source is low resolution. Use zoom 1.08 instead of 1.14, or a better clip. |
| Cutaway shows black | `from` + `len` is past the end of the b-roll file. Pick an earlier `from`. |
| Font not found | Fix the `fonts` paths (section 3). |
| Loud peak over -1.5 | Render again; if it stays, lower the opening shot `volume` to 0.4. |
| Whisper very wrong | In `reel.py words`, the model is "small". Add `"whisper_model": "medium"` to the config for better accuracy (slower). |

---

## 8. Deliver

1. Upload the finished mp4 to Frame.io, folder `Reels - finished` (create it if missing, inside the same project). Do not upload `band.mp4`, `sheet.jpg` or other working files.
2. Send the user a short message for each reel:
   ```
   Reel: <name>  (<length> s)
   Frame.io: <link>
   What it says: <one sentence>
   Instagram caption:
   <line 1>
   <line 2>
   #sales #salestraining #salescareer
   Checked: all boxes in section 7 passed.  (or say exactly which did not and why)
   ```
3. **Instagram caption rules:** 1 to 2 short lines, plain words, a question or a "save this" is fine. Max 3 to 5 hashtags. No emojis walls, no "link in bio" unless the user asks.

---

## 9. Reference

- Approved reel: `pov-final.mp4`. Its config is the example in 6.1.
- Style the user rates "really good": https://www.instagram.com/p/DaBVbJ3ocYU/ (big key words, zooms, cutaways). Use these ideas. Skip its money, car and house shots: there is no such footage, and it would not be true.
- Do not change the look values inside `reel.py` (sizes, colours, positions). They are the approved style. If you think something should change, ask the user first.
