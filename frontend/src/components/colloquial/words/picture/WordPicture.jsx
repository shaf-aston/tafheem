// Learn the words on a drawing: a body, a map, a family tree, a house, a clock and
// more. Explore first: tap any place and hear its name, see it in Arabic and English.
// Then Test: one word at a time, in Arabic with its sound; tap where it is. A right
// tap turns the place green; a wrong one shakes and says what was tapped, and shows
// the English as a hint; a second miss rings the right place, so a slip teaches. A warm-up like Match: nothing is filed
// for review. The boards and their spots are lib/colloquial/wordPictures.js.
import { useMemo, useRef, useState } from 'react'

import { pictureBoards } from '../../../../lib/colloquial/wordPictures'
import { speak } from '../../../../lib/speech/speak'
import { useAccent } from '../../../../lib/theme/accent'
import { shuffled } from '../../../../lib/text/shuffle'
import ArabicText from '../../../ui/ArabicText'
import Segmented from '../../../ui/Segmented'
import SmallButton from '../../../ui/SmallButton'
import SpeakButton from '../../../ui/SpeakButton'
import Spelling from '../../parts/Spelling'
import BodyArt from './BodyArt'
import MapArt from './MapArt'
import SceneArt from './SceneArt'

const STEPS = [{ id: 'explore', label: 'Explore' }, { id: 'test', label: 'Test' }]

const fresh = (board) => ({
  queue: shuffled(board.spots.flatMap((s) => s.words.map((word) => ({ word, key: s.key }))), Math.random),
  at: 0, found: [], slips: 0, misses: 0, tapped: null, wrong: false,
})

// Misses on one word before its place is shown.
const SHOW_AFTER = 2

// The spot under a tap: the country or dot tapped, else the nearest dot within reach.
function spotAt(event, board) {
  const named = event.target.closest?.('[data-key]')?.dataset.key
  if (named) return named
  const svg = event.currentTarget
  const point = new DOMPoint(event.clientX, event.clientY).matrixTransform(svg.getScreenCTM().inverse())
  const reach = board.view[2] * 0.1
  let best = null
  for (const s of board.spots) {
    const d = Math.hypot(s.x - point.x, s.y - point.y)
    if (d < reach && (!best || d < best.d)) best = { key: s.key, d }
  }
  return best?.key ?? null
}

// A place's words, all of them: "in" and "inside" share one panel.
function Said({ words }) {
  return (
    <div className="space-y-1">
      {words.map((w) => (
        <div key={w.id} className="flex items-center justify-center gap-3">
          <div>
            <ArabicText as="p" size="xl" className="text-[var(--text)]">{w.arabic}</ArabicText>
            <Spelling className="block">{w.transliteration}</Spelling>
            <p className="type-small text-[var(--text-dim)]">{w.english}</p>
          </div>
          <SpeakButton text={w.arabic} />
        </div>
      ))}
    </div>
  )
}

function Art({ board }) {
  if (board.art === 'map') return <MapArt view={board.view} keys={board.spots.map((s) => s.key)} />
  // Each draws only the boards it knows, and nothing for the rest.
  return <><BodyArt art={board.art} /><SceneArt board={board} /></>
}

export function Board({ board, step = 'test' }) {
  const [game, setGame] = useState(() => fresh(board))
  const [picked, setPicked] = useState(null)
  const accent = useAccent()
  const svg = useRef(null)
  const exploring = step === 'explore'
  const ask = game.queue[game.at]
  const done = !ask
  const r = board.view[2] / 30
  const tappedSpot = board.spots.find((s) => s.key === game.tapped)
  const pickedSpot = board.spots.find((s) => s.key === picked)

  const answer = (key) => {
    if (exploring) {
      const spot = board.spots.find((s) => s.key === key)
      if (!spot) return
      setPicked(key)
      // Heard as it is tapped; a voice that will not start leaves the words on screen.
      speak(spot.words[0].arabic, { accent }).catch(() => {})
      return
    }
    if (!key || done) return
    if (key === ask.key) {
      return setGame((g) => ({ ...g, at: g.at + 1, found: [...new Set([...g.found, key])], misses: 0, tapped: null, wrong: false }))
    }
    setGame((g) => ({ ...g, slips: g.slips + 1, misses: g.misses + 1, tapped: key, wrong: true }))
  }

  return (
    <div className="space-y-4">
      <div className="min-h-24 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4 flex items-center justify-center gap-3 text-center" aria-live="polite">
        {exploring ? (
          pickedSpot ? <Said words={pickedSpot.words} />
            : <span className="type-body text-[var(--text-dim)]">Tap any place to hear its name</span>
        ) : done ? (
          <span className="type-body font-medium text-[var(--text)]">All found · {game.slips} {game.slips === 1 ? 'slip' : 'slips'}</span>
        ) : (
          <>
            <div>
              <p className="type-micro text-[var(--text-faint)]">Where is</p>
              <ArabicText as="p" size="xl" className="text-[var(--text)]">{ask.word.arabic}</ArabicText>
              <Spelling className="block">{ask.word.transliteration}</Spelling>
              {game.wrong && <p className="type-small text-[var(--text-dim)]">{ask.word.english}</p>}
              {/* Said here, where the eye and the screen reader already are, not under the picture. */}
              {game.wrong && tappedSpot && <p className="type-small text-[var(--danger)]">
                You tapped <ArabicText as="span" size="sm">{tappedSpot.words[0].arabic}</ArabicText> ({tappedSpot.words[0].english})
                {game.misses >= SHOW_AFTER ? ': the ringed place is the one.' : '.'}
              </p>}
            </div>
            <SpeakButton text={ask.word.arabic} />
          </>
        )}
      </div>
      <svg ref={svg} viewBox={board.view.join(' ')} role="group" aria-label={`${board.label}: ${exploring ? 'tap a place to hear its name' : 'tap the place'}`}
        className="w-full max-w-md max-h-[70vh] mx-auto block touch-manipulation cursor-pointer select-none"
        onClick={(e) => answer(spotAt(e, board))}>
        <Art board={board} />
        {/* A led-out dot's line to its place, under the dots. */}
        {board.spots.filter((s) => s.to).map((s) => (
          <g key={`${s.key}-to`} aria-hidden="true" stroke="var(--text-dim)" strokeWidth={r / 6}>
            <line x1={s.x} y1={s.y} x2={s.to[0]} y2={s.to[1]} />
            <circle cx={s.to[0]} cy={s.to[1]} r={r / 3} fill="var(--text-dim)" />
          </g>
        ))}
        {/* After the misses run out, a ring around the place being asked for. */}
        {!exploring && ask && game.misses >= SHOW_AFTER && (() => {
          const s = board.spots.find((spot) => spot.key === ask.key)
          return s && <circle aria-hidden="true" cx={s.x} cy={s.y} r={r * 2.2} fill="none" stroke="var(--success)"
            strokeWidth={r / 3} strokeDasharray={`${r} ${r / 2}`} className="pointer-events-none" />
        })()}
        {/* Areas first, so a dot inside an area (a bed in the bedroom) is tapped over it. */}
        {[...board.spots].sort((a, b) => Boolean(b.area) - Boolean(a.area)).map((s) => {
          const i = board.spots.indexOf(s)
          const found = !exploring && game.found.includes(s.key)
          const wrong = !exploring && game.wrong && game.tapped === s.key
          const chosen = exploring && picked === s.key
          const ringed = !exploring && ask && game.misses >= SHOW_AFTER && ask.key === s.key
          const name = exploring ? s.words.map((w) => w.english).join(', ') : `Place ${i + 1}${found ? ', found' : ''}${ringed ? ', the ringed place' : ''}`
          const keys = { onKeyDown: (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); answer(s.key) } } }
          if (s.area) {
            const [x, y, w, h] = s.area
            const tint = found ? 'var(--success)' : wrong ? 'var(--danger)' : chosen ? 'var(--primary)' : null
            return (
              <rect key={s.key} data-key={s.key} x={x + 2} y={y + 2} width={w - 4} height={h - 4} rx={Math.min(8, w / 6)}
                role="button" tabIndex={0} aria-label={name} {...keys}
                className={`outline-none focus-visible:stroke-[var(--text)] ${wrong ? 'shake' : ''}`}
                fill={tint ? `color-mix(in oklab, ${tint} 18%, transparent)` : 'transparent'}
                // A faint dashed edge says the whole area can be tapped, without saying what it is.
                // (A grid's panels are already plainly cards, so they go without.)
                stroke={tint ?? (s.order ? 'transparent' : 'var(--border-hi)')} strokeOpacity={tint ? 1 : 0.6}
                strokeDasharray={tint ? undefined : `${r / 2} ${r / 2}`} strokeWidth={r / 5} />
            )
          }
          return (
            <circle key={s.key} data-key={s.key} cx={s.x} cy={s.y} r={wrong || chosen ? r * 1.3 : r}
              role="button" tabIndex={0} aria-label={name} {...keys}
              className={`outline-none focus-visible:stroke-[var(--text)] ${wrong ? 'shake' : ''}`}
              fill={found ? 'var(--success)' : wrong ? 'var(--danger)' : 'var(--primary)'}
              fillOpacity={exploring && !chosen ? 0.75 : 1}
              stroke="var(--surface)" strokeWidth={r / 3} />
          )
        })}
      </svg>
      {!exploring && <div className="flex flex-wrap items-center justify-between gap-3">
        <span className="type-small text-[var(--text-dim)]">
          {/* Counted in words: a place can hold two ("husband" and "brother-in-law"). */}
          {Math.min(game.at, game.queue.length)} of {game.queue.length} words · {game.slips} {game.slips === 1 ? 'slip' : 'slips'}
        </span>
        {done && <SmallButton onClick={() => setGame(fresh(board))}>Play again</SmallButton>}
      </div>}
    </div>
  )
}

export default function WordPicture({ words }) {
  const boards = useMemo(() => pictureBoards(words), [words])
  const [id, setId] = useState(boards[0]?.id)
  const [step, setStep] = useState('explore')
  const board = boards.find((b) => b.id === id) ?? boards[0]
  if (!board) return null
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        {boards.length > 1 ? (
          <Segmented label="Which picture" accent="var(--primary)" value={board.id} onChange={setId} wrap
            options={boards.map((b) => ({ id: b.id, label: b.label }))} />
        ) : <p className="eyebrow text-[var(--text-faint)]">{board.label}</p>}
        <Segmented label="Explore or test" accent="var(--primary)" value={step} onChange={setStep} compact options={STEPS} />
      </div>
      <Board key={`${board.id}-${step}`} board={board} step={step} />
    </div>
  )
}
