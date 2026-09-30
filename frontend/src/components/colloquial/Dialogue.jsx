// The dialogue as a stage: two speakers, one on each side, lines appearing as you tap through.
import { useState } from 'react'

import ArabicText from '../ui/ArabicText'
import PrimaryButton from '../ui/PrimaryButton'
import SmallButton from '../ui/SmallButton'
import Spelling from './Spelling'

const SIDE_TINT = ['--primary', '--warn']
const TINT_PERCENT = 18

const tone = (side) => `color-mix(in srgb, var(${SIDE_TINT[side]}) ${TINT_PERCENT}%, var(--surface-hi))`

function Speaker({ name, side, live }) {
  return (
    <div className={`flex flex-col items-center gap-1 ${live ? '' : 'opacity-60'} transition-opacity`}>
      <span
        aria-hidden="true"
        style={{ background: tone(side), borderColor: live ? `var(${SIDE_TINT[side]})` : 'var(--border)' }}
        className="w-12 h-12 grid place-items-center rounded-full border-2 type-ui font-semibold text-[var(--text)]"
      >
        {name[0]}
      </span>
      <span className="type-small text-[var(--text)]">{name}</span>
    </div>
  )
}

function Line({ line, side, latest }) {
  return (
    <li className={`flex ${side ? 'justify-end' : 'justify-start'} ${latest ? '' : 'opacity-70'}`}>
      <div
        style={{ background: tone(side) }}
        className={`max-w-[88%] px-4 py-3 space-y-1 border border-[var(--border)] rounded-[var(--radius-md)]
          ${side ? 'rounded-ee-none text-end' : 'rounded-es-none text-start'}`}
      >
        <ArabicText as="p" size="base" className="text-[var(--text)]">{line.arabic}</ArabicText>
        <Spelling className="block">{line.transliteration}</Spelling>
        <span className="block type-small text-[var(--text)]">{line.english}</span>
      </div>
    </li>
  )
}

export default function Dialogue({ lines }) {
  const [shown, setShown] = useState(0)
  const names = [...new Set(lines.map((l) => l.speaker))]
  const side = (name) => Math.min(names.indexOf(name), SIDE_TINT.length - 1)
  const live = shown ? lines[shown - 1].speaker : null
  const done = shown === lines.length

  return (
    <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
      <div className="flex justify-between px-6 py-4 border-b border-[var(--border)] bg-[var(--surface-hi)]">
        {names.slice(0, SIDE_TINT.length).map((n) => <Speaker key={n} name={n} side={side(n)} live={n === live} />)}
      </div>
      <ol aria-live="polite" className="p-4 space-y-3 min-h-40">
        {shown === 0 && <li className="type-small text-[var(--text-faint)] text-center py-8">The scene has not started.</li>}
        {lines.slice(0, shown).map((line, i) => (
          <Line key={i} line={line} side={side(line.speaker)} latest={i === shown - 1} />
        ))}
      </ol>
      <div className="flex items-center gap-3 p-4 border-t border-[var(--border)]">
        <div className="flex-1">
          <PrimaryButton onClick={() => setShown(shown + 1)} disabled={done}>
            {done ? 'The end' : shown ? 'Next line' : 'Start the scene'}
          </PrimaryButton>
        </div>
        <span className="type-small tabular-nums text-[var(--text-faint)]">{shown} / {lines.length}</span>
        <SmallButton onClick={() => setShown(done ? 0 : lines.length)}>{done ? 'Replay' : 'Show all'}</SmallButton>
      </div>
    </div>
  )
}
