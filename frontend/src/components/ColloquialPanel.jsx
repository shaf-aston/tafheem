/**
 * Colloquial: spoken Arabic, one step down at a time.
 *
 * Dialect, then unit, then topic, then the words. Only the current step is on
 * screen, with a trail above it to climb back up, so a learner is never shown
 * sixteen units and sixty topics at once. The catalogue (titles only) draws the
 * first three steps; the unit itself is fetched only once a topic is opened.
 */
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'

import { colloquialQuery, colloquialUnitQuery } from '../api'
import { warm } from '../lib/warm'
import { useRemembered } from '../lib/useRemembered'
import { colorFor } from '../theme'
import { FOCUS } from './colloquial/Face'
import UnitView from './colloquial/UnitView'
import WordBank from './colloquial/WordBank'
import ErrorAlert from './ui/ErrorAlert'
import SectionHeader from './ui/SectionHeader'
import { AnalyzerSkeleton } from './ui/Skeleton'

const HUES = 8
const unitNumber = (id) => Number(id.replace(/\D/g, '')) || 0

// A choice card: its colour glows in from both ends and fades to nothing in the middle.
// Without onClick it is a unit this dialect has not written yet: shown, not openable.
function Card({ hue, index, kicker, title, arabic, note, onClick }) {
  const tint = (pct) => `color-mix(in oklab, ${hue} ${pct}%, transparent)`
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!onClick}
      style={{
        '--i': index,
        background: `linear-gradient(90deg, ${tint(26)}, transparent 38%, transparent 62%, ${tint(26)}), var(--surface)`,
        borderColor: tint(40),
      }}
      className={`rise-in ${onClick ? 'lift press' : 'opacity-50 cursor-default'} group text-start w-full px-5 py-4 rounded-[var(--radius-lg)] border ${FOCUS}`}
    >
      <span className="flex items-baseline justify-between gap-3">
        <span className="type-micro uppercase tracking-[0.18em]" style={{ color: hue }}>{kicker}</span>
        {arabic && <span lang="ar" dir="rtl" className="arabic-sm text-[var(--text-dim)]">{arabic}</span>}
      </span>
      <span className="block type-ui font-semibold text-[var(--text)] mt-1">{title}</span>
      {note && <span className="block type-small text-[var(--text-faint)] mt-1">{note}</span>}
    </button>
  )
}

function Grid({ children }) {
  return <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">{children}</div>
}

// Where you are, each earlier step a button back to it.
function Trail({ steps }) {
  return (
    <nav aria-label="Where you are" className="flex flex-wrap items-center gap-x-2 gap-y-1 type-small">
      {steps.map((step, i) => {
        const last = i === steps.length - 1
        return (
          <span key={step.label} className="flex items-center gap-2">
            {i > 0 && <span aria-hidden className="text-[var(--text-faint)]">›</span>}
            {last
              ? <span aria-current="page" className="text-[var(--text)] font-medium">{step.label}</span>
              : <button type="button" onClick={step.go} className={`press text-[var(--text-dim)] hover:text-[var(--text)] underline-offset-4 hover:underline rounded ${FOCUS}`}>{step.label}</button>}
          </span>
        )
      })}
    </nav>
  )
}

// A quiet switch for learners who know more than one dialect: every dialect
// walks the same spine, so the same unit and topic are there to land on. A unit
// the other dialect has not written yet drops back to its unit list.
function Switch({ dialects, current, onPick }) {
  return (
    <label className="ms-auto flex items-center gap-2 type-small text-[var(--text-faint)]">
      <span>Same place in</span>
      <select value={current} onChange={(e) => onPick(e.target.value)}
        className={`bg-transparent text-[var(--text-dim)] hover:text-[var(--text)] rounded ${FOCUS}`}>
        {dialects.map((d) => <option key={d.key} value={d.key}>{d.label}</option>)}
      </select>
    </label>
  )
}

// The unit's word bank sits on the topic list; the unit loads once and is shared with the topics.
function UnitWordBank({ dialect, unit }) {
  const { data } = useQuery(colloquialUnitQuery(dialect, unit))
  return data ? <WordBank unit={data} /> : null
}

function Topic({ dialect, unit, at }) {
  const { data, isPending, isError, error, refetch } = useQuery(colloquialUnitQuery(dialect, unit))
  if (isPending) return <AnalyzerSkeleton />
  if (isError) return <ErrorAlert title="Could not load the lessons" fallback="The Colloquial lessons could not be reached." error={error} onRetry={refetch} />
  return <UnitView unit={data} at={at} />
}

export default function ColloquialPanel() {
  const catalogue = useQuery(colloquialQuery)
  const dialects = catalogue.data?.dialects ?? []
  const [dialectKey, setDialectKey] = useRemembered('colloq-dialect', dialects.map((d) => d.key))
  const [picked, setPicked] = useState(false)
  const [unitKey, setUnitKey] = useState(null)
  const [lessonAt, setLessonAt] = useState(null)
  const client = useQueryClient()

  const dialect = picked ? dialects.find((d) => d.key === dialectKey) : null
  const unit = dialect?.units.find((u) => u.written && u.unit === unitKey)
  // Opening a unit shows its topics; the unit's words are what a topic click needs.
  useEffect(() => {
    if (dialect && unit) warm(client, colloquialUnitQuery(dialect.key, unit.unit))
  }, [client, dialect, unit])
  const hue = unit ? colorFor('unit', unitNumber(unit.unit) % HUES) : null

  const toTop = () => { setPicked(false); setUnitKey(null); setLessonAt(null) }
  const toDialect = () => { setUnitKey(null); setLessonAt(null) }
  const toUnit = () => setLessonAt(null)
  const switchTo = (key) => {
    setDialectKey(key)
    if (!dialects.find((d) => d.key === key).units.some((u) => u.written && u.unit === unitKey)) toDialect()
  }

  const steps = [{ label: 'Dialects', go: toTop }]
  if (dialect) steps.push({ label: dialect.label, go: toDialect })
  if (unit) steps.push({ label: `Unit ${unitNumber(unit.unit)}`, go: toUnit })
  if (unit && lessonAt !== null) steps.push({ label: unit.lessons[lessonAt].title })

  return (
    <div className="panel">
      <SectionHeader title="Colloquial" arabic="عامية" subtitle={dialect?.where ?? 'Spoken, everyday Arabic.'} />
      {catalogue.isPending && <AnalyzerSkeleton />}
      {catalogue.isError && <ErrorAlert title="Could not load the lessons" fallback="The Colloquial lessons could not be reached." error={catalogue.error} onRetry={catalogue.refetch} />}
      {catalogue.data && (
        <div className="flex flex-wrap items-center gap-3">
          <Trail steps={steps} />
          {dialect && dialects.length > 1 && <Switch dialects={dialects} current={dialect.key} onPick={switchTo} />}
        </div>
      )}

      {catalogue.data && !dialect && (
        <Grid>
          {dialects.map((d, i) => (
            <Card key={d.key} index={i} hue={colorFor('tab', 'colloq')} kicker={d.where} title={d.label} arabic={d.arabic}
              note={`${d.units.filter((u) => u.written).length} units`} onClick={() => { setDialectKey(d.key); setPicked(true) }} />
          ))}
        </Grid>
      )}

      {dialect && !unit && (
        <Grid key={dialect.key}>
          {dialect.units.map((u, i) => (
            <Card key={u.unit} index={i} hue={colorFor('unit', unitNumber(u.unit) % HUES)}
              kicker={`Unit ${unitNumber(u.unit)}`} title={u.title}
              note={u.written ? u.lessons.map((l) => l.title).join(' · ') : 'Coming'}
              onClick={u.written ? () => setUnitKey(u.unit) : undefined} />
          ))}
        </Grid>
      )}

      {unit && lessonAt === null && (
        <div key={unit.unit} className="space-y-3">
          <div className="flex flex-wrap items-center gap-3">
            <h2 className="type-figure font-semibold text-[var(--text)]">{unit.title}</h2>
            <UnitWordBank dialect={dialect.key} unit={unit.unit} />
          </div>
          <Grid>
            {unit.lessons.map((l, i) => (
              <Card key={l.lesson} index={i} hue={hue} kicker={`Topic ${i + 1}`} title={l.title} onClick={() => setLessonAt(i)} />
            ))}
          </Grid>
        </div>
      )}

      {unit && lessonAt !== null && (
        <div key={`${unit.unit}/${lessonAt}`} className="rise-in">
          <Topic dialect={dialect.key} unit={unit.unit} at={lessonAt} />
        </div>
      )}
    </div>
  )
}
