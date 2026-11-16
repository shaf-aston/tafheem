# GRWTH reels: status (16 Nov 2026)

## Final versions (Frame.io, B ROLL project, folder "Reels - finished")
| Reel | File |
|---|---|
| pure-intent | 2026-11-16-pure-intent-v4.mp4 |
| 8k-no-sales-call | 2026-11-16-8k-no-sales-call-v6.mp4 |
| last-dollar | 2026-11-16-last-dollar-v5.mp4 |
| close-anywhere | 2026-11-16-close-anywhere-v4.mp4 |
| 25k-not-salesy | 2026-11-16-25k-not-salesy-v4.mp4 |
| ihsan-excellence | 2026-11-16-ihsan-excellence-v5.mp4 |
| time-over-money | 2026-11-16-time-over-money-v3.mp4 |

All older versions are in the subfolder "OLD VERSIONS - safe to delete" for you to delete. (ihsan v4 and last-dollar v4 were already deleted; they are in Frame.io Recently Deleted.)
The ad folder ("Mustafa / shayan - Grwth Ad") has not been touched.

## What's been done
- Full 9:16 frame, no black bars, no end card; last frame holds on a word card or b-roll.
- Hook title appears once as one block (no line-by-line popping).
- Every spoken word is captioned from 0 s to the end, on the chest/shirt (cap_y 0.72), never the mouth.
- Motion-graphic word cards (tools/mg.py) or fresh b-roll every 2-4 s; each b-roll shot used in one reel only.
- Voice chain for phone + earphones: 80 Hz high-pass, light denoise, -2.5 dB @250 Hz, +2.5 dB @3.5 kHz,
  -1.5 dB @7 kHz, 3:1 compression, mono-centred, loudnorm -14 LUFS, peaks under -1 dB.

## Checks run on every final
- Contact sheet every 0.5 s: no caption on mouth, no text off-screen, captions never overlap cards.
- Loudness -13.9 to -14.5 LUFS, peak -1.2 to -2.8 dBFS.
- Black/freeze/silence detection: only flags are the dark start of word cards (expected).

## Open points to check before posting
1. Listen on phone + earphones (sound measured, not heard).
2. time-over-money caption reads "none of that three matters" (transcription; confirm what he says).
3. time-over-money cafe shot shows another person in silhouette; confirm OK to show.
4. 8k uses a typing shot of a man in cap and beard; confirm OK to show.
5. Delete the folder "OLD VERSIONS - safe to delete" when ready.

## Rebuild
cd reels/<name> && python reel_local.py cut reel.json && python reel_local.py render reel.json
(media in src/ and mg/ is not in git; originals are in Frame.io)
