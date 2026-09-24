/**
 * The exercise library read by grammar point rather than drilled question by
 * question: a topic list sorted by how many questions cover it, the chosen
 * topic's meaning, and its rules and examples with Show answer toggles.
 */
import { useMemo, useState } from 'react'

import { answerParts, doubtsOf, labelOf, rowName } from '../lib/tamreen'
import { tagMatches } from '../lib/tamreenSearch'

import SearchBox from './ui/SearchBox'
import Disclosure from './ui/Disclosure'
import EmptyState from './ui/EmptyState'
import ArabicText from './ui/ArabicText'
import TamreenAnswerNote from './TamreenAnswerNote'
import TamreenSentence from './TamreenSentence'

function DoubtBadge({ example }) {
  if (doubtsOf(example).length === 0) return null
  return (
    <span
      className="type-small px-2 py-0.5 rounded-full border"
      style={{ color: 'var(--warn)', borderColor: 'color-mix(in srgb, var(--warn) 40%, transparent)' }}
    >
      Answer in doubt
    </span>
  )
}

export default function TamreenBrowse({ exercises, tags, coverage, accent }) {
  const [query, setQuery] = useState('')
  const [selectedKey, setSelectedKey] = useState(tags[0]?.key)

  const filteredTags = useMemo(
    () => tags
      .filter((t) => tagMatches(t, query))
      .sort((a, b) => (coverage[b.key] ?? 0) - (coverage[a.key] ?? 0)),
    [tags, coverage, query],
  )

  const selected = tags.find((t) => t.key === selectedKey) ?? filteredTags[0]

  const rules = useMemo(
    () => (selected ? exercises.flatMap((e) => e.rules.filter((r) => r.tags.includes(selected.key))) : []),
    [exercises, selected],
  )
  const examples = useMemo(
    () => (selected ? exercises.flatMap((e) => e.examples.filter((x) => x.tags.includes(selected.key))) : []),
    [exercises, selected],
  )

  return (
    <div className="grid gap-5 md:grid-cols-[240px_1fr] items-start">
      <div className="space-y-3">
        <SearchBox
          id="tamreen-topic-search"
          label="Find a grammar point"
          placeholder="e.g. haal, واو حالية"
          value={query}
          onChange={setQuery}
          accent={accent}
        />
        <nav className="flex flex-col gap-0.5" aria-label="Grammar points">
          {filteredTags.map((t) => {
            const on = t.key === selected?.key
            return (
              <button
                key={t.key}
                type="button"
                onClick={() => setSelectedKey(t.key)}
                aria-current={on ? 'true' : undefined}
                className={`flex items-center justify-between gap-2 px-2.5 py-1.5 rounded-[var(--radius-sm)] text-left transition-colors
                  ${on ? '' : 'text-[var(--text-faint)] hover:text-[var(--text-dim)]'}`}
                style={on ? { background: 'var(--surface-hi)', color: accent } : undefined}
              >
                <span className="flex items-baseline gap-1.5 min-w-0">
                  <ArabicText size="sm" className="shrink-0">{t.ar}</ArabicText>
                  <span className="type-small truncate">{t.en}</span>
                </span>
                <span className="type-small text-[var(--text-faint)] tabular-nums">{coverage[t.key] ?? 0}</span>
              </button>
            )
          })}
          {filteredTags.length === 0 && <EmptyState>No grammar point matches that.</EmptyState>}
        </nav>
      </div>

      {!selected ? (
        <EmptyState>Pick a grammar point to see its exercises.</EmptyState>
      ) : (
        <section className="space-y-4 min-w-0">
          <div>
            <h3 className="flex items-baseline gap-2 text-lg font-semibold">
              <ArabicText size="base">{selected.ar}</ArabicText>
              <span>{selected.en}</span>
            </h3>
            <p className="type-small text-[var(--text-dim)] mt-1">{selected.meaning}</p>
          </div>

          {rules.length > 0 && (
            <div className="space-y-2">
              <h4 className="type-tiny uppercase tracking-wide text-[var(--text-faint)]">Rules</h4>
              {rules.map((rule) => (
                <div key={rule.id} className="rounded-[var(--radius-md)] border border-[var(--border)] p-3 space-y-1.5">
                  <p dir="auto" className="font-medium">{rule.question}</p>
                  <Disclosure label="Show answer">
                    <ul className="space-y-1 mt-1.5">
                      {rule.options.map((option) => {
                        const right = rule.answer.includes(option)
                        return (
                          <li
                            key={option}
                            dir="auto"
                            className="type-small"
                            style={{ color: right ? 'var(--success)' : 'var(--text-faint)' }}
                          >
                            {right ? '✓' : '✗'} {option}
                          </li>
                        )
                      })}
                    </ul>
                  </Disclosure>
                </div>
              ))}
            </div>
          )}

          <div className="space-y-2">
            <h4 className="type-tiny uppercase tracking-wide text-[var(--text-faint)]">
              Examples · {examples.length}
            </h4>
            {examples.length === 0 && <EmptyState>No examples for this point.</EmptyState>}
            {examples.map((example) => (
              <div key={example.id} className="rounded-[var(--radius-md)] border border-[var(--border)] p-3 space-y-2">
                <TamreenSentence example={example} size="base" />
                <DoubtBadge example={example} />
                <Disclosure label="Show the teacher's answer">
                  <div className="space-y-2 mt-1.5">
                    {answerParts(example).map((part) => (
                      <dl key={part.letter} className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1">
                        {(part.rows ?? ['']).map((row) => (
                          <div key={row} className="contents">
                            <dt className="text-right"><ArabicText size="sm">{row && rowName(part, row)}</ArabicText></dt>
                            <dd className="text-right">
                              <ArabicText size="sm">
                                {((part.rows ? part.answer[row] : part.answer) ?? [])
                                  .map((option) => [option, labelOf(part, option)].filter(Boolean).join(' '))
                                  .join(' · ')}
                              </ArabicText>
                            </dd>
                          </div>
                        ))}
                      </dl>
                    ))}
                    <TamreenAnswerNote example={example} />
                  </div>
                </Disclosure>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
