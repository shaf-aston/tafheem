/**
 * Home: where the app opens. One thing to carry on with, and every tab under
 * its group, all in view.
 *
 * Where you stopped comes from the journey (lib/journey.js), never a list
 * written here; with no history, the first fixed tab (lib/tabs.js) stands in. The progress under each card is the overview the profile reads,
 * filed to tabs by lib/moduleTab.js. The line is the header's own command line.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { fetchOverview } from '../../lib/progress'
import { getProfile } from '../../lib/profile'
import { useRewards } from '../../lib/useRewards'
import { useHealth } from '../../lib/useHealth'
import { resumePlace, useJourney } from '../../lib/journey'
import { progressByTab } from '../../lib/moduleTab'
import { useCommandLine } from '../../lib/useCommandLine'
import { accentOf, FIXED, GROUPS, HOME, LISTED, RECENT, START } from '../../lib/tabs'
import { fill, greeting, progressText } from '../../lib/homeCopy'
import knobs from '../../home.json'

import ArabicText from '../ui/ArabicText'
import ErrorAlert from '../ui/ErrorAlert'
import { Skeleton } from '../ui/Skeleton'
import TabGroups from '../ui/TabGroups'
import CommandField from '../shell/CommandField'
import CommandResults from '../shell/CommandResults'
import ModuleCard from './ModuleCard'
import ProgressStrip from './ProgressStrip'
import ResumeCard from './ResumeCard'

const { copy } = knobs
const NAME = 'home'
const OTHERS = LISTED.filter((tab) => tab.id !== HOME)
const FALLBACK = FIXED.filter((id) => id !== HOME)
const KEY_COUNT = FIXED.length + RECENT.length
const tabOf = (id) => LISTED.find((tab) => tab.id === id)
const SHOWN_GROUPS = GROUPS.filter((group) => group.id !== START && OTHERS.some((tab) => tab.group === group.id))

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
  const card = (tab) => (
    <ModuleCard key={tab.id} tab={tab} accent={accentOf(tab.id)} progressText={progressText(sums[tab.id])} onOpen={onGo} />
  )

  const progressStrip = (
    <>
      {name && overview.isPending && <Skeleton className="h-16 w-full" />}
      {name && overview.isError && <ErrorAlert inline title={copy['progress-error']} onRetry={overview.refetch}>{copy['progress-error-body']}</ErrorAlert>}
      {!(name && (overview.isPending || overview.isError)) && (
        <ProgressStrip name={name} rewards={rewards} streak={overview.data?.streak} copy={copy} />
      )}
    </>
  )

  return (
    <div className="panel space-y-6" style={{ '--c': accent }}>
      <header className="relative isolate space-y-2">
        <ArabicText aria-hidden="true" className="outline-text hidden sm:block absolute -z-10 top-0 right-0 [--outline-size:6rem] leading-none pointer-events-none select-none">
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

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 md:items-start">
        <ResumeCard tab={lead} accent={accentOf(lead.id)} value={resume?.value}
          label={first ? copy['first-label'] : copy['resume-label']} goLabel={first ? copy['first-go'] : copy['resume-go']}
          progressText={progressText(sums[lead.id])} onGo={onGo} />
        <div className="min-w-0">{progressStrip}</div>
      </div>

      <section className="space-y-4" aria-labelledby="home-all">
        <h3 id="home-all" className="type-label font-bold uppercase tracking-widest text-[var(--primary-hi)]">
          {`${copy.all} (${OTHERS.length})`}
        </h3>
        <TabGroups groups={SHOWN_GROUPS} tabs={OTHERS} heading="h4" grid="gap-3 grid-cols-2 lg:grid-cols-3">
          {card}
        </TabGroups>
        <p className="type-small text-[var(--text-dim)] [@media(pointer:coarse)]:hidden">
          {fill(copy.keys, { n: KEY_COUNT })}
        </p>
      </section>
    </div>
  )
}
