/**
 * The time bar: drag along it and the map walks with you, one event at a time.
 *
 * Dragging only previews (onPreview), so the map and the bar follow the finger
 * while the reader below stays put; letting go opens the nearest event
 * (onPick). Arrow keys, Home and End, and the two buttons open the next event
 * at once. Where each event sits, and the year marks, are lib/timeline/time's.
 *
 * A dated section can be spread by true years or evenly, remembered; the
 * others are even only, so the choice is not offered.
 */
import { useState } from 'react'

import Segmented from '../ui/Segmented'
import SmallButton from '../ui/SmallButton'
import settings from '../../timelines.json'
import { nearest, positions, scaleModes, yearTicks } from '../../lib/timeline/time'
import { useRemembered } from '../../lib/useRemembered'

const { scrub: SCRUB } = settings
// The range input's resolution: fine enough that a drag feels continuous.
const STEPS = 1000
const KEYS = { ArrowRight: 1, ArrowUp: 1, PageUp: 1, ArrowLeft: -1, ArrowDown: -1, PageDown: -1 }

export default function TimelineScrub({ section, index, accent, onPreview, onPick }) {
  const modes = scaleModes(section)
  const [mode, setMode] = useRemembered('timeline-scale', modes)
  const [drag, setDrag] = useState(null)   // 0..1 while a finger is on the bar
  const pos = positions(section, mode)
  const last = section.events.length - 1
  const shown = drag === null ? index : nearest(pos, drag)
  const event = shown === null ? null : section.events[shown]
  const at = drag ?? (shown === null ? 0 : pos[shown])

  const open = (i) => onPick(section.events[Math.max(0, Math.min(last, i))].id)
  const move = (value) => {
    const f = value / STEPS
    setDrag(f)
    onPreview(nearest(pos, f))
  }
  const release = () => {
    if (drag === null) return
    open(nearest(pos, drag))
    setDrag(null)
    onPreview(null)
  }
  const onKeyDown = (e) => {
    const by = KEYS[e.key]
    const to = e.key === 'Home' ? 0 : e.key === 'End' ? last : by ? (index ?? -1) + by : null
    if (to === null) return
    e.preventDefault()
    open(to)
  }

  const marks = mode === 'years'
    ? yearTicks(section).map((t) => ({ key: t.year, at: t.at, text: t.year }))
    : []

  return (
    <div className="tl-scrub" style={{ '--tl-at': `${at * 100}%` }}>
      <div className="tl-scrub-head">
        <p className="tl-scrub-read" aria-live="polite">
          {event
            ? <><b>{event.when}</b> <span>{shown + 1} of {section.events.length}</span></>
            : <span>Drag along the bar to walk through {section.events.length} events</span>}
        </p>
        <div className="flex items-center gap-2 ml-auto">
          {modes.length > 1 && (
            <Segmented
              label="Spacing"
              compact
              accent={accent}
              value={mode}
              onChange={setMode}
              options={modes.map((id) => ({ id, label: SCRUB.modes[id] }))}
            />
          )}
          <SmallButton aria-label="Previous event" disabled={index === 0} onClick={() => open((index ?? 1) - 1)}>←</SmallButton>
          <SmallButton aria-label="Next event" disabled={index === last} onClick={() => open((index ?? -1) + 1)}>→</SmallButton>
        </div>
      </div>
      <div className="tl-scrub-track">
        <div className="tl-scrub-rail" />
        <div className="tl-scrub-fill" />
        {pos.map((p, i) => (
          <span key={section.events[i].id} className={`tl-scrub-tick${shown !== null && i <= shown ? ' on' : ''}`} style={{ left: `${p * 100}%` }} />
        ))}
        <div className="tl-scrub-thumb" />
        <input
          type="range"
          min={0}
          max={STEPS}
          value={Math.round(at * STEPS)}
          aria-label={`${section.name}: time`}
          aria-valuetext={event ? `${event.title}, ${event.when}` : 'No event open'}
          onChange={(e) => move(Number(e.target.value))}
          onPointerUp={release}
          onPointerCancel={release}
          onBlur={release}
          onKeyDown={onKeyDown}
        />
      </div>
      {marks.length > 0 && (
        <div className="tl-scrub-years" aria-hidden="true">
          {marks.map((m) => <span key={m.key} style={{ left: `${m.at * 100}%` }}>{m.text}</span>)}
        </div>
      )}
    </div>
  )
}
