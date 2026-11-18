/**
 * The course's three lists, one per level of the tree: dialects, a dialect's
 * units, a unit's topics. Each draws from the catalogue and moves with `go`.
 */
import { useQuery } from '@tanstack/react-query'

import { colloquialUnitQuery } from '../../../api'
import { nameOfPlace, parsePlace, unitNumber } from '../../../lib/colloquial/place'
import { isSeen, seenInUnit, topicsNote, useSeen } from '../../../lib/colloquial/seen'
import { colorAt, colorFor } from '../../../theme'
import { CountryIcons, CountryMap } from '../CountryMap'
import WordBank from '../words/WordBank'
import { Card, Grid, UnitCard, WordUnitCard } from './Cards'

// "16 of 19 units": the list below shows the unwritten ones too, marked Coming.
const unitsNote = (units) => {
  const written = units.filter((u) => u.written).length
  return written === units.length ? `${written} units` : `${written} of ${units.length} units`
}

// Where this device was last, if that topic is still there: one tap back to it. On the dialect list,
// and on a dialect's own page when the last topic is in it, so a learner arriving there resumes too.
function Continue({ dialects, go, only = null }) {
  const { last } = useSeen()
  const back = parsePlace(last, dialects)
  if (!back || typeof back.at !== 'number' || (only && back.dialect !== only)) return null
  const backDialect = dialects.find((d) => d.key === back.dialect)
  return (
    <div className="sm:max-w-md">
      <Card hue={colorFor('tab', 'colloq')} kicker="Continue where you left off" title={nameOfPlace(last, dialects)}
        note={`${backDialect.label} · Unit ${unitNumber(back.unit)}`} onClick={() => go(back)} />
    </div>
  )
}

export function DialectList({ dialects, go }) {
  const hue = colorFor('tab', 'colloq')
  return (
    <div className="space-y-4">
      <Continue dialects={dialects} go={go} />
      <Grid>
        {dialects.map((d) => (
          <Card key={d.key} hue={hue} kicker={d.where} title={d.label} gloss={d.gloss} arabic={d.arabic}
            note={unitsNote(d.units)} onClick={() => go({ dialect: d.key })}
            more={<CountryIcons codes={d.countries} />}
            picture={<CountryMap codes={d.countries} cities={d.cities} hue={hue} className="w-24 sm:w-32 shrink-0" />} />
        ))}
      </Grid>
    </div>
  )
}

// Talk units (phrases, a conversation, their words) and units of words alone are two
// shelves, so the two kinds never pass for each other. A dialect with one kind has one,
// unheaded. Numbering runs on across both, as in the spine.
const SHELVES = [
  { key: 'talk', title: 'Talk', note: 'Phrases, conversations and their words' },
  { key: 'words', title: 'Words', note: 'Words to learn by card, match and quiz' },
]
const shelfOf = (u) => (u.samples?.length ? 'words' : 'talk')

export function UnitList({ dialect, dialects = [dialect], go }) {
  const record = useSeen()
  const card = (u) => {
    const done = seenInUnit(record, dialect.key, u.unit)
    const hue = colorAt('unit', unitNumber(u.unit))
    const open = u.written ? () => go({ dialect: dialect.key, unit: u.unit }) : undefined
    if (shelfOf(u) === 'words') return <WordUnitCard key={u.unit} hue={hue} unit={u} done={done} onClick={open} />
    return u.written && u.cover
      ? <UnitCard key={u.unit} hue={hue} unit={u} done={done} onClick={open} />
      : <Card key={u.unit} hue={hue} kicker={`Unit ${unitNumber(u.unit)}`} title={u.title}
          note={u.written ? topicsNote(u.lessons.length, done) : 'Coming'} onClick={open} />
  }
  const shelves = SHELVES.map((s) => ({ ...s, units: dialect.units.filter((u) => shelfOf(u) === s.key) })).filter((s) => s.units.length)
  const resume = <Continue dialects={dialects} go={go} only={dialect.key} />
  if (shelves.length < 2) return <div className="space-y-4">{resume}<Grid>{dialect.units.map(card)}</Grid></div>
  return (
    <div className="space-y-6">
      {resume}
      {shelves.map((s) => (
        <section key={s.key} className="space-y-2" aria-labelledby={`shelf-${s.key}`}>
          <div className="flex flex-wrap items-baseline gap-x-3">
            <h2 id={`shelf-${s.key}`} className="type-ui font-semibold text-[var(--text)]">{s.title}</h2>
            <span className="type-small text-[var(--text-faint)]">
              Units {unitNumber(s.units[0].unit)}–{unitNumber(s.units.at(-1).unit)} · {s.note}
            </span>
          </div>
          <Grid>{s.units.map(card)}</Grid>
        </section>
      ))}
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

// The unit's word bank sits on the topic list; the unit loads once and is shared with the topics.
function UnitWordBank({ dialect, unit }) {
  const { data, isError } = useQuery(colloquialUnitQuery(dialect, unit))
  if (isError) return <span className="type-small text-[var(--text-faint)]">The word bank did not load.</span>
  return data ? <WordBank unit={data} /> : null
}

// A topic with phrases and words is a twin card: its phrases one half, its words the other.
export function TopicList({ dialect, unit, go }) {
  const record = useSeen()
  const hue = colorAt('unit', unitNumber(unit.unit))
  const open = (at, words, mode) => go({ dialect: dialect.key, unit: unit.unit, at, words, ...(mode ? { mode } : {}) })
  return (
    <div className="space-y-3">
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
                <Card key={l.lesson} hue={hue} kicker={`Topic ${i + 1}${isSeen(record, dialect.key, unit.unit, l.lesson) ? ' · Seen' : ''}`} title={l.title} image={l.picture}
                  note={!l.written ? 'Coming' : !l.phrases ? `${l.words} words${l.sentences ? ` · ${l.sentences} sentences` : ''} · Pictures · Cards · Quiz` : l.words ? `${l.phrases} phrases · practice` : undefined}
                  onClick={l.written ? () => open(i, !l.phrases) : undefined}
                  twin={l.written && l.phrases > 0 && l.words > 0 && { kicker: 'Words', title: `${l.words} to learn`, onClick: () => open(i, true),
                    // Straight to a way of learning them: one tap, not the list and then a tab.
                    actions: [{ label: 'Cards', onClick: () => open(i, true, 'cards') }, { label: 'Quiz', onClick: () => open(i, true, 'quiz') }] }} />
              )
            })}
          </Grid>
        </div>
      ))}
    </div>
  )
}
