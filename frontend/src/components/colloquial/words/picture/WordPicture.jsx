// Match the word to the picture: one word at a time, in Arabic with its sound; tap
// where it is on the drawing (a body part, or a country on the map). A right tap turns
// the dot green; a wrong one shakes and says what was tapped, and shows the English
// as a hint, so a slip teaches. A warm-up like Match: nothing is filed for review.
// The boards and their spots are lib/colloquial/wordPictures.js.
import { useMemo, useRef, useState } from 'react'

import { pictureBoards } from '../../../../lib/colloquial/wordPictures'
import { shuffled } from '../../../../lib/text/shuffle'
import ArabicText from '../../../ui/ArabicText'
import Segmented from '../../../ui/Segmented'
import SmallButton from '../../../ui/SmallButton'
import SpeakButton from '../../../ui/SpeakButton'
import Spelling from '../../parts/Spelling'
import BodyArt from './BodyArt'
import MapArt from './MapArt'

const fresh = (board) => ({
  queue: shuffled(board.spots.flatMap((s) => s.words.map((word) => ({ word, key: s.key }))), Math.random),
  at: 0, found: [], slips: 0, tapped: null, wrong: false,
})

// The spot under a tap: the country or dot tapped, else the nearest dot within reach.
function spotAt(event, board) {
  const named = event.target.closest?.('[data-key]')?.dataset.key
  if (named) return named
  const svg = event.currentTarget
  const point = new DOMPoint(event.clientX, event.clientY).matrixTransform(svg.getScreenCTM().inverse())
  const reach = board.view[2] * 0.08
  let best = null
  for (const s of board.spots) {
    const d = Math.hypot(s.x - point.x, s.y - point.y)
    if (d < reach && (!best || d < best.d)) best = { key: s.key, d }
  }
  return best?.key ?? null
}

export function Board({ board }) {
  const [game, setGame] = useState(() => fresh(board))
  const svg = useRef(null)
  const ask = game.queue[game.at]
  const done = !ask
  const r = board.view[2] / 40
  const tappedSpot = board.spots.find((s) => s.key === game.tapped)

  const answer = (key) => {
    if (!key || done) return
    if (key === ask.key) {
      return setGame((g) => ({ ...g, at: g.at + 1, found: [...new Set([...g.found, key])], tapped: null, wrong: false }))
    }
    setGame((g) => ({ ...g, slips: g.slips + 1, tapped: key, wrong: true }))
  }

  return (
    <div className="space-y-4">
      <div className="min-h-24 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4 flex items-center justify-center gap-3 text-center" aria-live="polite">
        {done ? (
          <span className="type-body font-medium text-[var(--text)]">All found · {game.slips} {game.slips === 1 ? 'slip' : 'slips'}</span>
        ) : (
          <>
            <div>
              <p className="type-micro text-[var(--text-faint)]">Where is</p>
              <ArabicText as="p" size="xl" className="text-[var(--text)]">{ask.word.arabic}</ArabicText>
              <Spelling className="block">{ask.word.transliteration}</Spelling>
              {game.wrong && <p className="type-small text-[var(--text-dim)]">{ask.word.english}</p>}
            </div>
            <SpeakButton text={ask.word.arabic} />
          </>
        )}
      </div>
      <svg ref={svg} viewBox={board.view.join(' ')} role="group" aria-label={`${board.label}: tap the place`}
        className="w-full max-w-md mx-auto block touch-manipulation cursor-pointer select-none"
        onClick={(e) => answer(spotAt(e, board))}>
        {board.art === 'map' ? <MapArt view={board.view} keys={board.spots.map((s) => s.key)} /> : <BodyArt art={board.art} />}
        {board.spots.map((s, i) => {
          const found = game.found.includes(s.key)
          const wrong = game.wrong && game.tapped === s.key
          return (
            <circle key={s.key} data-key={s.key} cx={s.x} cy={s.y} r={wrong ? r * 1.3 : r}
              role="button" tabIndex={0} aria-label={`Place ${i + 1}${found ? ', found' : ''}`}
              className={`outline-none focus-visible:stroke-[var(--text)] ${wrong ? 'shake' : ''}`}
              fill={found ? 'var(--success)' : wrong ? 'var(--danger)' : 'var(--primary)'}
              stroke="var(--surface)" strokeWidth={r / 3}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); answer(s.key) } }} />
          )
        })}
      </svg>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <span className="type-small text-[var(--text-dim)]">
          {game.wrong && tappedSpot && <>That is <ArabicText as="span" size="base">{tappedSpot.words[0].arabic}</ArabicText> ({tappedSpot.words[0].english}). </>}
          {Math.min(game.at, game.queue.length)} of {game.queue.length} · {game.slips} {game.slips === 1 ? 'slip' : 'slips'}
        </span>
        {done && <SmallButton onClick={() => setGame(fresh(board))}>Play again</SmallButton>}
      </div>
    </div>
  )
}

export default function WordPicture({ words }) {
  const boards = useMemo(() => pictureBoards(words), [words])
  const [id, setId] = useState(boards[0]?.id)
  const board = boards.find((b) => b.id === id) ?? boards[0]
  if (!board) return null
  return (
    <div className="space-y-4">
      {boards.length > 1 && (
        <Segmented label="Which picture" accent="var(--primary)" value={board.id} onChange={setId}
          options={boards.map((b) => ({ id: b.id, label: b.label }))} />
      )}
      <Board key={board.id} board={board} />
    </div>
  )
}
