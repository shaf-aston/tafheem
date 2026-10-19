/**
 * Home: where the app opens. One thing to carry on with, a few recent tabs,
 * and every tab behind "All sections".
 *
 * Where you stopped and the recent tabs come from the journey (lib/journey.js),
 * never a list written here; with no history, the fixed tabs (lib/tabs.js)
 * stand in. The progress under each card is the overview the profile reads,
 * filed to tabs by lib/moduleTab.js. The line is the header's own command line.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { fetchOverview } from '../../lib/progress'
import { getProfile } from '../../lib/profile'
import { useRewards } from '../../lib/useRewards'
import { useHealth } from '../../lib/useHealth'
import { jumpTabs, resumePlace, useJourney } from '../../lib/journey'
import { progressByTab } from '../../lib/moduleTab'
import { useCommandLine } from '../../lib/useCommandLine'
import { accentOf, FIXED, GROUPS, HOME, LISTED, RECENT, START } from '../../lib/tabs'
import knobs from '../../home.json'

import ArabicText from '../ui/ArabicText'
import Disclosure from '../ui/Disclosure'
import ErrorAlert from '../ui/ErrorAlert'
import { Skeleton } from '../ui/Skeleton'
import CommandField from '../shell/CommandField'
import CommandResults from '../shell/CommandResults'
import ModuleCard from './ModuleCard'
import JumpTile from './JumpTile'
import ProgressStrip from './ProgressStrip'
import ResumeCard from './ResumeCard'

const { copy } = knobs
const NAME = 'home'
const OTHERS = LISTED.filter((tab) => tab.id !== HOME)
const FALLBACK = FIXED.filter((id) => id !== HOME)
const KEY_COUNT = FIXED.length + RECENT.length
const tabOf = (id) => LISTED.find((tab) => tab.id === id)
const fill = (line, values) => line.replace(/\{(\w+)\}/g, (_, key) => values[key])
const greeting = () => {
  const hour = new Date().getHours()
  return (knobs.greetings.find((one) => hour < one.until) ?? knobs.greetings.at(-1)).text
}

function progressText(sum) {
  if (!sum) return null
  return `${fill(copy.learnt, sum)} · ${fill(sum.attempts === 1 ? copy['answers-one'] : copy['answers-many'], { n: sum.attempts })}`
}

export default function HomePanel({ accent, onGo }) {
  const [name] = useState(getProfile)
  const overview = useQuery({ queryKey: ['overview', name], queryFn: fetchOverview, enabled: !!name, retry: false })
  const { rewards } = useRewards(name)
  const { steps } = useJourney()
  const health = useHealth()
  const line = useCommandLine(LISTED, (row) => onGo(row.tabId, row.value))
  const sums = progressByTab(overview.data?.modules)
  const showing = line.rows.length > 0
  const offline = health.status === 'error'

  const resume = resumePlace(steps, LISTED, HOME)
  const first = !resume
  const lead = tabOf(resume?.tab ?? FALLBACK[0])
  const tiles = jumpTabs(steps, {
    listed: LISTED, fallback: FALLBACK, home: HOME, skip: lead.id, pin: offline ? knobs['offline-pin'] : null,
    count: first ? knobs['tiles-first'] : knobs.tiles,
  })
  const jumpLabel = first ? copy['jump-first'] : copy['jump-resume']

  return (
    <div className="panel space-y-6" style={{ '--c': accent }}>
      <header className="relative space-y-2">
        <ArabicText aria-hidden="true" className="absolute -top-2 end-0 text-[clamp(6rem,24vw,12rem)] leading-none pointer-events-none select-none"
          style={{ color: 'transparent', WebkitTextStroke: '1.5px color-mix(in srgb, var(--primary) 30%, transparent)' }}>
          فهم
        </ArabicText>
        <p className="rise-in type-label font-bold uppercase tracking-widest text-[var(--primary-hi)]">{first ? copy['greeting-first'] : greeting()}</p>
        <h2 className="rise-in text-3xl sm:text-5xl font-semibold leading-tight" style={{ '--i': 1 }}>
          {first ? copy['title-first'] : copy['title-resume']}
        </h2>
        <p className="rise-in relative text-[var(--text-dim)] max-w-[46ch]" style={{ '--i': 2 }}>
          {first ? copy['welcome-first'] : copy['welcome-resume']}
        </p>
      </header>

      {offline && (
        <ErrorAlert title={copy['offline-title']} onRetry={health.retryHealth}>{copy['offline-body']}</ErrorAlert>
      )}

      <div className="cb" data-wide>
        <CommandField line={line} name={NAME} placeholder={copy.placeholder} showing={showing} />
        {showing && (
          <CommandResults id={`${NAME}-results`} name={NAME} rows={line.rows} tabs={LISTED} colorOf={accentOf}
            active={line.active} onHover={line.setActive} onPick={line.run}
            railTab={line.rows[line.active]?.tabId} onRail={(id) => onGo(id)} />
        )}
      </div>

      <div className="grid gap-6 md:grid-cols-[1.15fr_1fr]">
        <ResumeCard tab={lead} accent={accentOf(lead.id)} value={resume?.value}
          label={first ? copy['first-label'] : copy['resume-label']} goLabel={first ? copy['first-go'] : copy['resume-go']}
          progressText={progressText(sums[lead.id])} onGo={onGo} />

        <section className="space-y-2" aria-label={jumpLabel}>
          <h3 className="type-label font-bold uppercase tracking-widest text-[var(--primary-hi)]">{jumpLabel}</h3>
          {health.status === 'checking' ? (
            <div className="grid grid-cols-2 gap-3" role="status" aria-label={copy['progress-loading']}>
              {tiles.map((id) => <Skeleton key={id} className="h-24" />)}
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              {tiles.map((id, at) => <JumpTile key={id} tab={tabOf(id)} accent={accentOf(id)} index={at} onOpen={onGo} />)}
            </div>
          )}
          <p className="type-small text-[var(--text-dim)] [@media(pointer:coarse)]:hidden">
            {fill(copy.keys, { n: KEY_COUNT })}
          </p>
        </section>
      </div>

      {name && overview.isPending && <Skeleton className="h-16 w-full" />}
      {name && overview.isError && <ErrorAlert inline error={overview.error} fallback={copy['progress-error']} onRetry={overview.refetch} />}
      {!(name && (overview.isPending || overview.isError)) && (
        <ProgressStrip name={name} rewards={rewards} streak={overview.data?.streak} copy={copy} />
      )}

      <Disclosure tone="strong" label={`${copy.all} (${OTHERS.length})`} className="[&_summary]:min-h-11">
        <div className="space-y-4 pt-2">
          {GROUPS.filter((group) => group.id !== START).map((group) => (
            <section key={group.id} className="space-y-2" aria-label={group.label}>
              <h3 className="type-small font-bold text-[var(--text-dim)]">{group.label}</h3>
              <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
                {OTHERS.filter((tab) => tab.group === group.id).map((tab) => (
                  <ModuleCard key={tab.id} tab={tab} accent={accentOf(tab.id)} progressText={progressText(sums[tab.id])} onOpen={onGo} />
                ))}
              </div>
            </section>
          ))}
        </div>
      </Disclosure>
    </div>
  )
}
