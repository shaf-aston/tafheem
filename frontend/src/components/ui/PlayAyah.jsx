/**
 * Hear this ayah recited. One button, play and stop in the same place.
 *
 * The recording is a plain file on a public CDN, worked out from the ayah's own
 * numbers, so pressing this is one request and the sound starts while the rest
 * of the file is still arriving. lib/ayahAudio.js holds all of that; this is
 * only the button.
 *
 * Every one of these shares a single player, so starting one ayah stops
 * whichever was talking, and a reading view full of them still owns one.
 */
import { useEffect, useState, useSyncExternalStore } from 'react'

import { ayahAudioUrl, nowPlaying, play, prefetch, stop, watch } from '../../lib/ayahAudio'

export default function PlayAyah({ surah, ayah, reciter, accent, src, eager = false, className = '' }) {
  // `src` where the caller knows which recording it is lighting words against;
  // worked out here where nobody is following the words and any copy will do.
  const url = src ?? ayahAudioUrl(surah, ayah, reciter)
  // Read from the player rather than kept here, so this is right the moment it
  // renders. Switching reciter changes this button's url without anything
  // starting or stopping, and a copy updated by events alone sat on the word
  // Stop for a recording it no longer named.
  const current = useSyncExternalStore(watch, nowPlaying, () => '')
  const playing = current === url
  const [failed, setFailed] = useState(false)

  // The ayah being looked at is very likely the one that will be played, so its
  // recording is started early. Only where a page shows one ayah: doing it for
  // every row of a surah would fetch a hundred megabytes nobody asked for.
  useEffect(() => {
    if (eager) prefetch(url)
  }, [eager, url])

  const press = () => {
    if (playing) return stop()
    setFailed(false)
    play(url).catch(() => setFailed(true))
  }

  return (
    <span className="inline-flex items-center gap-2">
      <button
        type="button"
        onClick={press}
        onPointerEnter={() => prefetch(url)}
        style={{ '--c': accent }}
        aria-label={playing ? `Stop ${surah}:${ayah}` : `Play ${surah}:${ayah}`}
        title={failed ? 'That recitation could not be reached' : playing ? 'Stop' : 'Play the recitation'}
        className={`shrink-0 w-7 h-7 grid place-items-center rounded-full border transition-colors
          ${playing
            ? 'text-[var(--c)] border-[var(--c)] bg-[color-mix(in_srgb,var(--c)_16%,transparent)]'
            : 'text-[var(--text-faint)] border-[var(--border)] hover:text-[var(--text)] hover:border-[var(--border-hi)]'}
          ${failed ? 'text-[var(--warn)] border-[var(--warn)]' : ''} ${className}`}
      >
        {playing ? <StopGlyph /> : <PlayGlyph />}
      </button>
      {/* Visible, not just a title tooltip: a failed fetch otherwise looks like
          the button did nothing. */}
      {failed && (
        <span className="type-small text-[var(--warn)]" aria-live="polite">
          That recitation could not be reached
        </span>
      )}
    </span>
  )
}

function PlayGlyph() {
  return (
    <svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor" aria-hidden="true">
      <path d="M7 4.5v15l13-7.5z" />
    </svg>
  )
}

function StopGlyph() {
  return (
    <svg viewBox="0 0 24 24" width="11" height="11" fill="currentColor" aria-hidden="true">
      <rect x="5" y="5" width="14" height="14" rx="2.5" />
    </svg>
  )
}
