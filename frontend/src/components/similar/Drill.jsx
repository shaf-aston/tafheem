import { useMemo, useState } from 'react'

import { colorFor } from '../../theme'
import { makeRandom } from '../../lib/memorise'
import { drillOf, fill, whereOf } from '../../lib/similar'
import copy from '../../similar.json'

import ArabicText from '../ui/ArabicText'
import EmptyState from '../ui/EmptyState'
import PrimaryButton from '../ui/PrimaryButton'

const COLOR = { self: colorFor('similar', 'mine'), other: colorFor('similar', 'twin') }

/**
 * The verse with one difference taken out: the gap shows "?" until answered, then
 * the right words. A "what comes next" question has its gap after the last word.
 */
function GapVerse({ question, answered }) {
  const { words, span, marked } = question
  const tone = answered === null ? 'var(--primary-hi)' : answered ? 'var(--success)' : 'var(--danger)'
  const gap = (
    <span
      key="gap"
      className="inline-block min-w-16 px-2 text-center border-b-2 border-dashed rounded-t-[var(--radius-sm)]"
      style={{ borderColor: tone, color: tone, background: `color-mix(in srgb, ${tone} 12%, transparent)` }}
    >
      {answered === null ? '?' : question.right || '∅'}
    </span>
  )
  const near = (w) => marked.some(([s, e]) => w >= s && w < e)
  const out = []
  for (let w = 0; w <= words.length; w += 1) {
    if (w === span[0]) out.push(gap)
    if (w < words.length && (w < span[0] || w >= span[1])) {
      out.push(<ArabicText key={w} size="base" className={near(w) ? 'text-[var(--text)]' : 'text-[var(--text-dim)]'}>{words[w]}</ArabicText>)
    }
  }
  return <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1" dir="rtl">{out}</div>
}

/**
 * Each difference asked in turn, from one verse and then the other: its own
 * wording against its twin's. A slip shows where the wrong words come from,
 * which is the thing being learnt. `onDone(correct)` files the whole pair;
 * `seed` deals the order of the two options.
 */
export default function Drill({ mine, partner, seed, accent, onDone, onCompare, onNext }) {
  // Which side each right answer sits on: shuffled per round, so its place is no clue.
  const questions = useMemo(() => {
    const random = makeRandom(seed)
    return drillOf(mine, partner).map((q) => ({ ...q, flip: random() < 0.5 }))
  }, [mine, partner, seed])
  const [at, setAt] = useState(0)
  const [answered, setAnswered] = useState(null)
  const [slips, setSlips] = useState(0)

  if (questions.length === 0) return <EmptyState>{copy['no-drill']}</EmptyState>

  const q = questions[at]
  if (!q) {
    const passed = slips === 0
    return (
      <div className="space-y-3">
        <p className="rounded-[var(--radius-sm)] p-3 text-[var(--text)]" style={{ background: passed ? 'var(--success-wash)' : 'var(--danger-wash)' }}>
          {passed ? copy.passed : fill(copy.slipped, { n: slips })}
        </p>
        <PrimaryButton accent={accent} onClick={passed ? onNext : onCompare}>{passed ? copy['next-pair'] : copy.again}</PrimaryButton>
      </div>
    )
  }

  const side = q.key === mine.key ? 'self' : 'other'
  const [before, after] = (q.next ? copy['ask-next'] : copy.ask).split('{where}')
  const options = [{ words: q.right, right: true }, { words: q.wrong, right: false }]
  if (q.flip) options.reverse()
  const choose = (right) => {
    setAnswered(right)
    if (!right) setSlips((n) => n + 1)
  }
  const next = () => {
    setAnswered(null)
    setAt(at + 1)
    if (at + 1 === questions.length) onDone(slips === 0)
  }

  return (
    <div className="space-y-3">
      <h3 className="eyebrow">{fill(copy.question, { n: at + 1, of: questions.length })}</h3>
      <p className="type-small text-[var(--text-dim)]">
        {before}<b style={{ color: COLOR[side] }}>{whereOf(q.key)}</b>{after}
      </p>
      <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--bg)] p-3 sm:p-4">
        <GapVerse question={q} answered={answered} />
      </div>
      {answered === null ? (
        <div className="grid grid-cols-2 gap-2">
          {options.map((o) => (
            <button
              key={String(o.right)}
              type="button"
              data-similar-option=""
              onClick={() => choose(o.right)}
              className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-hi)] px-3 py-2 hover:border-[var(--border-hi)] text-center"
            >
              {o.words
                ? <ArabicText size="base" className="text-[var(--text)]">{o.words}</ArabicText>
                : <span className="type-small italic text-[var(--text-faint)]">{q.next ? copy.end : copy.nothing}</span>}
            </button>
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          <p className="rounded-[var(--radius-sm)] p-3 type-small text-[var(--text)]" style={{ background: answered ? 'var(--success-wash)' : 'var(--danger-wash)' }}>
            {answered ? copy.right : fill(copy.wrong, { where: whereOf(q.twin) })}
          </p>
          <PrimaryButton accent={accent} onClick={next}>{copy.next}</PrimaryButton>
        </div>
      )}
    </div>
  )
}
