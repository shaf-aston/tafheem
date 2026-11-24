# Tafheem launch video

A 30-second launch video made in code with [Remotion](https://www.remotion.dev): 1920 × 1080 at 60 fps,
plus 9:16 and 1:1 cutdowns from the same scenes. The UI is drawn as vectors (no screenshots), the
fonts and colours are the app's own (`frontend/src/config/theme.json`, the Ink look), and the
soundtrack is synthesised from the same timeline as the picture.

## Make it

```bash
npm install
python3 scripts/soundtrack.py                      # music bed + UI sounds → public/audio/soundtrack.wav
npx remotion studio                                # preview and scrub
npx remotion render Launch out/tafheem-launch-1080p.mp4
npx remotion render LaunchVertical out/tafheem-launch-9x16.mp4
npx remotion render LaunchSquare out/tafheem-launch-1x1.mp4
node scripts/stills.mjs 290 760 1330               # quick stills of chosen frames → out/stills/
```

In a container without Chrome downloads, point Remotion at a local headless Chrome with
`REMOTION_CHROME=/path/to/chrome-headless-shell`.

## Change it

| To change | Edit |
|---|---|
| Any words, the counter target, colours | `src/config.js` (one line each) |
| When anything happens, and its sound | `src/timeline.json`, then re-run `scripts/soundtrack.py` |
| How a scene looks or moves | `src/scenes/<Scene>.jsx` |

## Storyboard

30.0 s · 1920 × 1080 · 60 fps · 1800 frames

**Scene 1 · Hook** — 0:00–0:05.5, frames 0–330
- On screen: warm paper, an eight-point star drawing itself and turning. ٱقْرَأْ inks in, "Read." (Al-'Alaq 96:1). The question types out: "But do you understand what you read?" An iris of ink opens from the centre: "Meet [mark] Tafheem", تفهيم under it.
- Motion: star outlines draw on; the word scales in from a blur; type-on with caret; the mark spins in with overshoot and the words slide out from behind it.
- Camera: slow push 100% → 114% through the paper, then a micro-push on the logo.

**Scene 2 · Problem** — 0:05.5–0:10.5, frames 330–630
- On screen: a pile of windows (Lisan al-Arab, Lane, a grammar PDF, a translation, a search, a tafsir). "Ten tabs open. *Still no why.*" The pile is pulled into one bar; the sentence إِنَّ الطَّالِبَ الْمُجْتَهِدَ كَتَبَ الرِّسَالَةَ فِي الْمَكْتَبَةِ الْكَبِيرَةِ types in; the cursor arcs over, hesitates, clicks Analyse.
- Motion: windows drop in staggered with overshoot; headline word by word; windows exit fast, ease-in, into the centre; button press 1 → 0.96 → 1.
- Camera: zoom into the bar while typing, ease back on the click.

**Scene 3 · Feature demo** — 0:10.5–0:20.5, frames 630–1230
- On screen: eight word cards with their roles (from the landing page's real analysis); joins drawn under them up to جُمْلَةٌ اسْمِيَّةٌ; إِنَّ reaching the noun it makes accusative; "Read by the grammar books' rules · no AI guessing". Push into كَتَبَ: the root ك ت ب and the six words it grows, then the four dictionaries. Then reciting Al-'Alaq 96:1: the cursor switches on "Works offline" (gold glow), presses the mic, and each word turns green with a check.
- Motion: cards every 6 frames; brackets draw on; root words fly out on dashed lines; book cards staggered; toggle with neon glow; waveform.
- Camera: push into the verb card to change beat; pull back for the root; drift to the toggle and back.

**Scene 4 · Payoff** — 0:20.5–0:30, frames 1230–1800
- On screen: a wall of dots, "Opening the corpus", then 0 → 6,236 "ayahs, every word with its grammar" and "34 classical books · 4 dictionaries · every answer cites its source". The study dashboard: eight tools, Today's list, level bar, "Words understood today" tile last. The bar types "Now I understand what I read." (the answer to the hook) and Send is clicked. Paper irises out of the button: the mark draws, Tafheem, تفهيم, "Read the Qur'an. Understand every word.", tafheem-app.vercel.app.
- Motion: counter eases up over 1 s; tiles and rows cascade; counter tile lands last; logo builds from its outline.
- Camera: pull back as the dashboard resolves, push toward Send, then a slow push on the logo.
