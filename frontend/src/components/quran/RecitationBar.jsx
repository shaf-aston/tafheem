import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from 'react'

import { RECITERS, nowPlaying, play, prefetch, stop, watch, watchEnd } from '../../lib/ayahAudio'
import WheelPicker from '../ui/WheelPicker'

// The reciters as the dropdown's choices, each with its Arabic name beside it.
const VOICES = RECITERS.map((one) => ({ id: one.id, label: one.name, hint: one.arabic }))

export const PLAY = 'M7 4.5v15l13-7.5z'

/**
 * The one player for the surah, held to the bottom of the screen: back, play or
 * stop, on, and who is reciting. Playing runs on through the surah an ayah at a
 * time, and the list follows while the reader is following it.
 *
 * Who is reciting is the app's one dropdown (ui/WheelPicker), opening upwards
 * from the bar; its pill already names the voice, so the line beside the
 * buttons says only where the recitation is.
 */
export default function RecitationBar({ surah, count, from, here, recitation, reciter, onReciter, onFollow, startRef }) {
  const now = useSyncExternalStore(watch, nowPlaying, () => '')
  const [failed, setFailed] = useState(false)
  // The ayah last started and the address it was started on. Matched by that
  // address, not by asking the recitation again: the measured recording can
  // arrive mid-ayah and change what urlFor answers, but not what is playing.
  const [cue, setCue] = useState(null)
  const sounding = now && now === cue?.url ? cue.n : 0
  const at = sounding || from
  const { urlFor } = recitation

  const start = useCallback((n) => {
    if (n < 1 || n > count) return
    const url = urlFor(n)
    setFailed(false)
    setCue({ n, url })
    // A press that overtakes the last one aborts it; only a refusal is a failure.
    play(url).catch((e) => e.name !== 'AbortError' && setFailed(true))
  }, [count, urlFor])
  // The header starts it from outside; a new voice picks up the same ayah
  // rather than stopping, so the bar is not gone from under the choice.
  const playing = useRef({ start, sounding })
  useEffect(() => {
    playing.current = { start, sounding }
    startRef.current = start
  })
  useEffect(() => {
    const { start: again, sounding: n } = playing.current
    if (n) again(n)
  }, [reciter])
  // A skip is the reader moving, so the list and rail go with it.
  const skipTo = (n) => { start(n); onFollow(n) }

  // On to the next ayah when one ends; the list follows only if the reader was
  // still with the one that finished, never pulled away from where they went.
  useEffect(() => watchEnd((url) => {
    if (url !== cue?.url || cue.n >= count) return
    start(cue.n + 1)
    if (Math.abs(here - cue.n) <= 1) onFollow(cue.n + 1)
  }), [cue, start, onFollow, here, count])
  // Stop when the bar goes with its surah, so nothing plays on under another.
  useEffect(() => () => stop(), [])

  // Reading somewhere else while it recites: the place it is at becomes a way
  // back there, pointing up or down to it. Same reach as the follow above.
  const away = sounding && Math.abs(here - sounding) > 1

  const round = 'press shrink-0 grid place-items-center rounded-full transition-colors'
  // Only while it recites, or to say why it could not.
  if (!sounding && !failed) return null
  const skip = `${round} w-8 h-8 text-[var(--text-dim)] hover:text-[var(--text)] disabled:opacity-30`

  return (
    <div className="reader-dock rise-in flex items-center gap-2 p-2 pl-3 border-t border-[var(--border)] bg-[var(--surface-hi)]">
      <button type="button" className={skip}
        onClick={() => skipTo(at - 1)} disabled={at <= 1} aria-label="Previous ayah">
        <Glyph d="M6 5h2v14H6zM20 5v14L9 12z" />
      </button>
      <button type="button" className={`${round} w-10 h-10 text-[var(--bg)] bg-[var(--c)]`}
        onClick={() => (sounding ? stop() : start(at))} onPointerEnter={() => prefetch(urlFor(at))}
        aria-label={sounding ? `Stop ${surah}:${sounding}` : `Play from ${surah}:${at}`}>
        <Glyph d={sounding ? 'M6 6h12v12H6z' : PLAY} />
      </button>
      <button type="button" className={skip}
        onClick={() => skipTo(at + 1)} disabled={at >= count} aria-label="Next ayah">
        <Glyph d="M16 5h2v14h-2zM4 5v14l11-7z" />
      </button>

      <p className="min-w-0 flex-1 truncate type-small" aria-live="polite">
        {failed ? (
          <span className="text-[var(--warn)]">That recitation could not be reached</span>
        ) : away ? (
          <button type="button" onClick={() => onFollow(sounding)}
            aria-label={`Go to ${surah}:${sounding}, being recited`}
            className="fade-in press inline-flex items-center gap-1 px-2.5 py-1 rounded-full font-mono text-[var(--bg)] bg-[var(--c)]">
            <Glyph d={sounding < here ? 'M12 5l7 8h-5v6h-4v-6H5z' : 'M12 19l7-8h-5V5h-4v6H5z'} />
            {/* The ayah alone: the bar only plays its own surah, and 2:255 in full would not fit a phone. */}
            {sounding}
          </button>
        ) : (
          <span className="font-mono text-[var(--text)]">{surah}:{at}</span>
        )}
      </p>

      <WheelPicker label="Reciter" options={VOICES} value={reciter} onChange={onReciter} className="shrink-0" />
    </div>
  )
}

export function Glyph({ d }) {
  return (
    <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true"><path d={d} /></svg>
  )
}
