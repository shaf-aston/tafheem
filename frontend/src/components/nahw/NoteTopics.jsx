/**
 * Picking a notes topic, laid out like a book's contents: a list beside the
 * reading on wide screens, one dropdown above it on a phone. Each topic shows
 * both names, so two topics sharing an Arabic name (notes and worksheet) differ.
 */
import { useEffect, useRef } from 'react'

import ArabicText from '../ui/text/ArabicText'

const pagesOf = (n) => `${n} ${n === 1 ? 'page' : 'pages'}`

export function TopicList({ topics, current, onPick }) {
  // The open topic kept in view, since a long list scrolls inside itself.
  const list = useRef(null)
  useEffect(() => {
    list.current?.querySelector('[aria-current]')?.scrollIntoView({ block: 'nearest' })
  }, [current])
  return (
    <nav
      ref={list}
      aria-label="Topics"
      // The fade at the foot says the list goes on below.
      className="hidden lg:block sticky top-24 max-h-[calc(100vh-7rem)] overflow-y-auto pe-1 pb-8 [mask-image:linear-gradient(to_bottom,black_calc(100%-3rem),transparent)]"
    >
      <ol className="space-y-0.5">
        {topics.map((t) => {
          const on = t.id === current
          return (
            <li key={t.id}>
              <button
                type="button"
                onClick={() => onPick(t.id)}
                aria-current={on ? 'page' : undefined}
                className={`w-full text-start rounded-[var(--radius-md)] px-3 py-2 border-s-2 transition-colors ${
                  on
                    ? 'border-[var(--c)] bg-[color-mix(in_srgb,var(--c)_12%,transparent)]'
                    : 'border-transparent hover:bg-[var(--surface-hi)]'
                }`}
              >
                <ArabicText size="sm" className={`block text-end ${on ? 'text-[var(--c)] font-semibold' : ''}`}>{t.arabic}</ArabicText>
                <span className="block type-small text-[var(--text-faint)]">{t.title} · {pagesOf(t.pages)}</span>
              </button>
            </li>
          )
        })}
      </ol>
    </nav>
  )
}

export function TopicSelect({ topics, current, onPick }) {
  return (
    <label className="lg:hidden flex flex-col gap-1 type-small text-[var(--text-dim)]">
      Topic
      <select
        value={current}
        onChange={(e) => onPick(e.target.value)}
        className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-hi)] text-[var(--text)] px-3 py-2 text-base"
      >
        {topics.map((t) => <option key={t.id} value={t.id}>{t.arabic} — {t.title}</option>)}
      </select>
    </label>
  )
}

// The end of a topic leads on to its neighbours, so reading through needs no trip back to the top.
export function TopicSteps({ topics, current, onPick }) {
  const at = topics.findIndex((t) => t.id === current)
  const step = (t, label, align) => t && (
    <button
      type="button"
      aria-label={`${label}: ${t.title}`}
      onClick={() => {
        onPick(t.id)
        // To the new topic's heading, focus and all, so keyboard and screen reader land there too.
        requestAnimationFrame(() => document.getElementById('note-topic')?.focus())
      }}
      className={`flex-1 rounded-[var(--radius-md)] border border-[var(--border)] px-3 py-2 hover:bg-[var(--surface-hi)] ${align}`}
    >
      <span className="block type-small text-[var(--text-faint)]">{label}</span>
      <ArabicText size="sm" className="block">{t.arabic}</ArabicText>
      <span className="block type-small text-[var(--text-faint)]">{t.title}</span>
    </button>
  )
  return (
    <div className="flex gap-2 pt-4 border-t border-[var(--border)]">
      {step(topics[at - 1], 'Previous', 'text-start')}
      {step(topics[at + 1], 'Next', 'text-end ms-auto')}
    </div>
  )
}
