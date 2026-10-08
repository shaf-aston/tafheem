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
import { nameOfPlace, parsePlace, placeOf } from '../lib/colloquialPlace'
import { useArrivalWhenReady } from '../lib/useArrival'
import { warm } from '../lib/warm'
import { useRemembered } from '../lib/useRemembered'
import { colorFor } from '../theme'
import { FOCUS } from './colloquial/Face'
import PhrasePicture from './colloquial/PhrasePicture'
import UnitView from './colloquial/UnitView'
import WordBank from './colloquial/WordBank'
import WordsView from './colloquial/WordsView'
import ArabicText from './ui/ArabicText'
import ErrorAlert from './ui/ErrorAlert'
import SectionHeader from './ui/SectionHeader'
import SpeakButton from './ui/SpeakButton'
import WheelPicker from './ui/WheelPicker'
import { AnalyzerSkeleton } from './ui/Skeleton'

const HUES = 8
const unitNumber = (id) => Number(id.replace(/\D/g, '')) || 0

// A choice card: its colour glows in from both ends and fades to nothing in the middle.
// Without onClick it is a unit or topic this dialect has not written yet: shown, not openable.
// With `twin` it is two halves joined, each its own way in: a topic's phrases and its words.
function Lines({ hue, kicker, title, arabic, note }) {
  return (
    <>
      <span className="flex items-baseline justify-between gap-3">
        <span className="type-micro uppercase tracking-[0.18em]" style={{ color: hue }}>{kicker}</span>
        {arabic && <span lang="ar" dir="rtl" className="arabic-sm text-[var(--text-dim)]">{arabic}</span>}
      </span>
      <span className="block type-ui font-semibold text-[var(--text)] mt-1">{title}</span>
      {note && <span className="block type-small text-[var(--text-faint)] mt-1">{note}</span>}
    </>
  )
}

const lookOf = (hue, index) => {
  const tint = (pct) => `color-mix(in oklab, ${hue} ${pct}%, transparent)`
  return {
    '--i': index,
    background: `linear-gradient(90deg, ${tint(26)}, transparent 38%, transparent 62%, ${tint(26)}), var(--surface)`,
    borderColor: tint(40),
  }
}

function Card({ hue, index, onClick, twin, ...lines }) {
  const look = lookOf(hue, index)
  const half = `lift press group text-start w-full px-5 py-4 ${FOCUS}`
  if (twin) {
    return (
      <div style={look} className="rise-in grid grid-cols-2 rounded-[var(--radius-lg)] border overflow-hidden">
        <button type="button" onClick={onClick} aria-label={`${lines.title}: ${lines.note}`} className={half}><Lines hue={hue} {...lines} /></button>
        <button type="button" onClick={twin.onClick} aria-label={`${lines.title}: ${twin.title} ${twin.kicker.toLowerCase()}`} className={`${half} border-s`} style={{ borderColor: look.borderColor }}>
          <Lines hue={hue} {...twin} />
        </button>
      </div>
    )
  }
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!onClick}
      style={look}
      className={`rise-in ${onClick ? 'lift press' : 'opacity-50 cursor-default'} group text-start w-full px-5 py-4 rounded-[var(--radius-lg)] border ${FOCUS}`}
    >
      <Lines hue={hue} {...lines} />
    </button>
  )
}

// A written unit opens on its cover phrase: said aloud, its picture filling the card's
// whole empty lower left, out to the border, so no word sits on it. It takes the height
// the words make and never adds its own (contain: size). The whole card opens the unit; the speaker is
// drawn above that and only speaks, the words beside it letting a click through.
function UnitCard({ hue, index, unit, onClick }) {
  const { cover } = unit
  const number = unitNumber(unit.unit)
  return (
    <div style={lookOf(hue, index)} className="rise-in lift press relative grid grid-cols-[minmax(0,2fr)_minmax(0,3fr)] grid-rows-[auto_auto_1fr_auto] gap-x-3.5 px-5 py-4 rounded-[var(--radius-lg)] border">
      <button type="button" onClick={onClick} aria-label={`Unit ${number}: ${unit.title}`} className={`stretch absolute inset-0 rounded-[var(--radius-lg)] ${FOCUS}`} />
      <span className="col-span-2 flex items-baseline justify-between gap-3 type-micro uppercase tracking-[0.18em]">
        <span style={{ color: hue }}>Unit {number}</span>
        <span className="text-[var(--text-faint)]">{unit.lessons.length} topics</span>
      </span>
      <span className="col-span-2 type-ui font-semibold text-[var(--text)] mt-1">{unit.title}</span>
      <PhrasePicture phrase={cover} alt="" className="soft-edge pointer-events-none row-span-2 self-stretch [contain:size] mt-2 -ms-5 -mb-4 rounded-es-[calc(var(--radius-lg)-1px)] w-[calc(100%+1.25rem)] max-w-none" />
      <span className="relative pointer-events-none self-end flex items-center gap-3 mt-2">
        <SpeakButton text={cover.arabic} className="pointer-events-auto" />
        <ArabicText className="flex-1 min-w-0 text-start [overflow-wrap:anywhere]">{cover.arabic}</ArabicText>
      </span>
      <span className="type-small text-[var(--text-faint)] text-end">{cover.english}</span>
    </div>
  )
}

// Neighbouring topics under one heading; a unit without sections is one run with no heading.
function sectionsOf(lessons) {
  return lessons.reduce((runs, l, i) => {
    const last = runs.at(-1)
    if (last && last.section === (l.section ?? null)) last.lessons.push(l)
    else runs.push({ section: l.section ?? null, from: i, lessons: [l] })
    return runs
  }, [])
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
    <div className="ms-auto flex items-center gap-2 type-small text-[var(--text-faint)]">
      <span>Same place in</span>
      <WheelPicker label="Dialect" options={dialects.map((d) => ({ id: d.key, label: d.label }))}
        value={current} onChange={onPick} accent={colorFor('tab', 'colloq')} />
    </div>
  )
}

// The unit's word bank sits on the topic list; the unit loads once and is shared with the topics.
function UnitWordBank({ dialect, unit }) {
  const { data } = useQuery(colloquialUnitQuery(dialect, unit))
  return data ? <WordBank unit={data} /> : null
}

function Topic({ dialect, unit, at, words }) {
  const { data, isPending, isError, error, refetch } = useQuery(colloquialUnitQuery(dialect, unit))
  if (isPending) return <AnalyzerSkeleton />
  if (isError) return <ErrorAlert title="Could not load the lessons" fallback="The Colloquial lessons could not be reached." error={error} onRetry={refetch} />
  return words ? <WordsView unit={data} at={at} /> : <UnitView unit={data} at={at} />
}

export default function ColloquialPanel({ incoming, arrival, onVisit }) {
  const catalogue = useQuery(colloquialQuery)
  const dialects = catalogue.data?.dialects ?? []
  const [dialectKey, setDialectKey] = useRemembered('colloq-dialect', dialects.map((d) => d.key))
  const [picked, setPicked] = useState(false)
  const [unitKey, setUnitKey] = useState(null)
  const [lessonAt, setLessonAt] = useState(null)
  const [words, setWords] = useState(false)
  const client = useQueryClient()

  const dialect = picked ? dialects.find((d) => d.key === dialectKey) : null
  const unit = dialect?.units.find((u) => u.written && u.unit === unitKey)
  // Opening a unit shows its topics; the unit's words are what a topic click needs.
  useEffect(() => {
    if (dialect && unit) warm(client, colloquialUnitQuery(dialect.key, unit.unit))
  }, [client, dialect, unit])
  const hue = unit ? colorFor('unit', unitNumber(unit.unit) % HUES) : null

  // One way to move: every step down or up the tree is a place on the journey,
  // so a reload, a pasted link and the back arrow all land where the reader was.
  const show = (there) => {
    setPicked(Boolean(there))
    if (there) setDialectKey(there.dialect)
    setUnitKey(there?.unit ?? null)
    setLessonAt(there?.at ?? null)
    setWords(there?.words ?? false)
  }
  const go = (dialectK = null, unitK = null, at = null, wordsToo = false) => {
    show(dialectK && { dialect: dialectK, unit: unitK, at, words: wordsToo })
    const lessonK = at === null ? null : dialects.find((d) => d.key === dialectK).units.find((u) => u.unit === unitK).lessons[at].lesson
    onVisit?.(dialectK ? placeOf(dialectK, unitK, lessonK, wordsToo) : null)
  }
  // An arrival names a place; followed during render so a reload paints on it, not the top first.
  if (useArrivalWhenReady(arrival, Boolean(catalogue.data))) show(parsePlace(incoming, dialects))

  const toTop = () => go()
  const toDialect = () => go(dialect.key)
  const toUnit = () => go(dialect.key, unit.unit)
  // The same unit and topic in the other dialect, if that one has written them.
  const switchTo = (key) => {
    const there = dialects.find((d) => d.key === key).units.find((u) => u.written && u.unit === unitKey)
    const kept = lessonAt !== null && there?.lessons[lessonAt].written ? lessonAt : null
    go(key, there ? unitKey : null, there ? kept : null, kept !== null && words && there.lessons[kept].words > 0)
  }

  const steps = [{ label: 'Dialects', go: toTop }]
  if (dialect) steps.push({ label: dialect.label, go: toDialect })
  if (unit) steps.push({ label: `Unit ${unitNumber(unit.unit)}`, go: toUnit })
  if (unit && lessonAt !== null) steps.push({ label: unit.lessons[lessonAt].title, go: () => go(dialect.key, unit.unit, lessonAt) })
  if (unit && lessonAt !== null && words) steps.push({ label: 'Words' })

  return (
    <div className="panel">
      <SectionHeader title="Colloquial" arabic="عامية" subtitle={dialect?.where ?? 'Spoken, everyday Arabic.'}
        nameOf={(q) => nameOfPlace(q, dialects)} />
      {catalogue.isPending && <AnalyzerSkeleton />}
      {catalogue.isError && <ErrorAlert title="Could not load the lessons" fallback="The Colloquial lessons could not be reached." error={catalogue.error} onRetry={catalogue.refetch} />}
      {catalogue.data && (
        <div className="flex flex-wrap items-center gap-3 pb-5 border-b border-[var(--border)]">
          <Trail steps={steps} />
          {dialect && dialects.length > 1 && <Switch dialects={dialects} current={dialect.key} onPick={switchTo} />}
        </div>
      )}

      {catalogue.data && !dialect && (
        <Grid>
          {dialects.map((d, i) => (
            <Card key={d.key} index={i} hue={colorFor('tab', 'colloq')} kicker={d.where} title={d.label} arabic={d.arabic}
              note={`${d.units.filter((u) => u.written).length} units`} onClick={() => go(d.key)} />
          ))}
        </Grid>
      )}

      {dialect && !unit && (
        <Grid key={dialect.key}>
          {dialect.units.map((u, i) => {
            const unitHue = colorFor('unit', unitNumber(u.unit) % HUES)
            return u.written && u.cover
              ? <UnitCard key={u.unit} index={i} hue={unitHue} unit={u} onClick={() => go(dialect.key, u.unit)} />
              : <Card key={u.unit} index={i} hue={unitHue} kicker={`Unit ${unitNumber(u.unit)}`} title={u.title}
                  note={u.written ? `${u.lessons.length} topics` : 'Coming'}
                  onClick={u.written ? () => go(dialect.key, u.unit) : undefined} />
          })}
        </Grid>
      )}

      {unit && lessonAt === null && (
        <div key={unit.unit} className="space-y-3">
          <div className="flex flex-wrap items-center gap-3">
            <h2 className="type-figure font-semibold text-[var(--text)]">{unit.title}</h2>
            <UnitWordBank dialect={dialect.key} unit={unit.unit} />
          </div>
          {sectionsOf(unit.lessons).map(({ section, from, lessons }) => (
            <div key={from} className="space-y-2">
              {section && <h3 className="type-small font-semibold text-[var(--text-dim)] pt-4">{section}</h3>}
              <Grid>
                {lessons.map((l, n) => {
                  const i = from + n
                  return (
                    <Card key={l.lesson} index={i} hue={hue} kicker={`Topic ${i + 1}`} title={l.title}
                      note={!l.written ? 'Coming' : l.words ? 'Phrases' : undefined}
                      onClick={l.written ? () => go(dialect.key, unit.unit, i) : undefined}
                      twin={l.written && l.words > 0 && { kicker: 'Words', title: `${l.words} to learn`, note: 'Cards · quiz', onClick: () => go(dialect.key, unit.unit, i, true) }} />
                  )
                })}
              </Grid>
            </div>
          ))}
        </div>
      )}

      {unit && lessonAt !== null && (
        <div key={`${unit.unit}/${lessonAt}/${words}`} className="rise-in">
          <Topic dialect={dialect.key} unit={unit.unit} at={lessonAt} words={words} />
        </div>
      )}
    </div>
  )
}
