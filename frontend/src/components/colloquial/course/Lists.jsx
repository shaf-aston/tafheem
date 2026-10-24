/**
 * The course's three lists, one per level of the tree: dialects, a dialect's
 * units, a unit's topics. Each draws from the catalogue and moves with `go`.
 */
import { useQuery } from '@tanstack/react-query'

import { colloquialUnitQuery } from '../../../api'
import { unitNumber } from '../../../lib/colloquial/place'
import { colorAt, colorFor } from '../../../theme'
import { CountryIcons, CountryMap } from '../CountryMap'
import WordBank from '../words/WordBank'
import { Card, Grid, UnitCard } from './Cards'

// "16 of 19 units": the list below shows the unwritten ones too, marked Coming.
const unitsNote = (units) => {
  const written = units.filter((u) => u.written).length
  return written === units.length ? `${written} units` : `${written} of ${units.length} units`
}

export function DialectList({ dialects, go }) {
  const hue = colorFor('tab', 'colloq')
  return (
    <Grid>
      {dialects.map((d, i) => (
        <Card key={d.key} index={i} hue={hue} kicker={d.where} title={d.label} gloss={d.gloss} arabic={d.arabic}
          note={unitsNote(d.units)} onClick={() => go({ dialect: d.key })}
          more={<CountryIcons codes={d.countries} />}
          picture={<CountryMap codes={d.countries} cities={d.cities} hue={hue} className="w-24 sm:w-32 shrink-0" />} />
      ))}
    </Grid>
  )
}

export function UnitList({ dialect, go }) {
  return (
    <Grid key={dialect.key}>
      {dialect.units.map((u, i) => {
        const hue = colorAt('unit', unitNumber(u.unit))
        const open = u.written ? () => go({ dialect: dialect.key, unit: u.unit }) : undefined
        return u.written && u.cover
          ? <UnitCard key={u.unit} index={i} hue={hue} unit={u} onClick={open} />
          : <Card key={u.unit} index={i} hue={hue} kicker={`Unit ${unitNumber(u.unit)}`} title={u.title}
              note={u.written ? `${u.lessons.length} topics` : 'Coming'} onClick={open} />
      })}
    </Grid>
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
  const { data } = useQuery(colloquialUnitQuery(dialect, unit))
  return data ? <WordBank unit={data} /> : null
}

// A topic with phrases and words is a twin card: its phrases one half, its words the other.
export function TopicList({ dialect, unit, go }) {
  const hue = colorAt('unit', unitNumber(unit.unit))
  const open = (at, words) => go({ dialect: dialect.key, unit: unit.unit, at, words })
  return (
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
                <Card key={l.lesson} index={i} hue={hue} kicker={`Topic ${i + 1}`} title={l.title} image={l.picture}
                  note={!l.written ? 'Coming' : !l.phrases ? `${l.words} words` : l.words ? 'Phrases' : undefined}
                  onClick={l.written ? () => open(i, !l.phrases) : undefined}
                  twin={l.written && l.phrases > 0 && l.words > 0 && { kicker: 'Words', title: `${l.words} to learn`, note: 'Cards · quiz', onClick: () => open(i, true) }} />
              )
            })}
          </Grid>
        </div>
      ))}
    </div>
  )
}
