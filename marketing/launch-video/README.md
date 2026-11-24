# Tafheem launch video

A 24-second launch video made in code with [Remotion](https://www.remotion.dev): 1920 × 1080 at 60 fps,
plus 9:16 and 1:1 versions from the same shots. It follows the shot rhythm of a fast "AI product reveal"
(16 shots, a cut every ~1.5 s, typed prompts, a cursor that clicks, a counter, a dashboard, a logo
sting), filled with Tafheem's own content: real app screenshots, a real Qur'an folio, the eight real
tools and Al-'Alaq 96:1 analysed word by word. The soundtrack is synthesised from the same timeline.

## Make it

```bash
npm install
python3 scripts/soundtrack.py                      # music + UI sounds → public/audio/soundtrack.wav
npx remotion studio                                # preview and scrub
npx remotion render Launch out/tafheem-launch-1080p.mp4
npx remotion render LaunchVertical out/tafheem-launch-9x16.mp4
npx remotion render LaunchSquare out/tafheem-launch-1x1.mp4
node scripts/stills.mjs Launch 170 815 1200        # quick stills of chosen frames → out/stills/
```

In a container without Chrome downloads, point Remotion at a local headless Chrome with
`REMOTION_CHROME=/path/to/chrome-headless-shell`. Remotion writes full-range colour; for social
uploads re-encode with `ffmpeg -i in.mp4 -pix_fmt yuv420p -movflags +faststart out.mp4`.

## Change it

| To change | Edit |
|---|---|
| Any words, cards, tools, dashboard numbers, colours | `src/config.js` |
| When anything happens, and its sound | `src/timeline.json`, then re-run `scripts/soundtrack.py` |
| How a shot looks or moves | `src/shots/<File>.jsx` (see the table below) |
| Shared pieces (orb, bubbles, toggle, cursor, cards, tiles) | `src/ui/Kit.jsx` |
| Pictures | `public/img/` (app screenshots + the Met folio) |

Layout: shots are drawn on a 1920 × 1080 canvas with the key content inside the centre 1440 × 1080.
`Stage` scales that to any output; `useFit(width)` shrinks wide rows on 9:16 and 1:1.

## Storyboard

24.0 s · 60 fps · 1440 frames

| # | Frames | Shot | File |
|---|---|---|---|
| 1 | 0–120 | Tunnel of eight-point stars; "Do you understand what you recite?" types in; zoom through | `Open.jsx` Tunnel |
| 2 | 120–200 | "Meet [orb] Tafheem" pulls into focus from a blur | `Open.jsx` Meet |
| 3 | 200–245 | Orb steps aside; a big glass bubble types "Salaam" | `Open.jsx` Hello |
| 4 | 245–360 | Chat: Tafheem offers help, the student asks for the ayah word by word | `Chat.jsx` Chat |
| 5 | 360–510 | Prompt bar types "Break down every word of this ayah"; a hand drags in the folio and two app screens; click send | `Chat.jsx` Prompt |
| 6 | 510–600 | The i'rab of 96:1 streams by like code | `Engine.jsx` Stream |
| 7 | 600–675 | "Connect the classical books" — the cursor flips the switch | `Engine.jsx` Connect |
| 8 | 675–750 | Book tiles, letters and screens join up: "Connecting 34 books" | `Engine.jsx` Web |
| 9 | 750–820 | Three tool cards (Nahw, Sarf, Qur'an) switch on | `Tools.jsx` Cards |
| 10 | 820–870 | The eight tools pop in | `Tools.jsx` Icons |
| 11 | 870–930 | Tafheem's page for Al-'Alaq: ٱقْرَأْ, the folio, four screens | `Tools.jsx` Page |
| 12 | 930–1000 | Halftone dot rows: "Counting every word" | `Proof.jsx` Dots |
| 13 | 1000–1060 | The folio with a counter 0 → 6,236 "ayahs, word by word" | `Proof.jsx` Folio |
| 14 | 1060–1230 | Dashboard builds: tool cards, lessons, words today, day streak | `Proof.jsx` Dash |
| 15 | 1230–1350 | White bar types "Now I understand what I read. Let's keep going"; camera leans into send; click | `Close.jsx` Final |
| 16 | 1350–1440 | ✕ turns into +, the star draws round it, "Tafheem", tafheem-app.vercel.app | `Close.jsx` Logo |

The dashboard numbers (16 words today, 40-day streak) are demo values, set in `DASH` in `src/config.js`.
