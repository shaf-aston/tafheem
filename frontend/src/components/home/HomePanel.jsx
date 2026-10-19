/**
 * Home: the first screen, and the way into every tab on phone and desktop.
 *
 * The cards come from the tab registry (lib/tabs.js), so a new tab appears here
 * with no edit. The progress under each card is the overview the profile reads,
 * filed to tabs by lib/moduleTab.js. The line is the header's own command line.
 * Continue lists the last places visited in other tabs (lib/journey.js).
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { fetchOverview } from '../../lib/progress'
import { getProfile } from '../../lib/profile'
import { useRewards } from '../../lib/useRewards'
import { useJourney } from '../../lib/journey'
import { progressByTab } from '../../lib/moduleTab'
import { useCommandLine } from '../../lib/useCommandLine'
import { accentOf, GROUPS, LISTED } from '../../lib/tabs'
import knobs from '../../home.json'

import SectionHeader from '../ui/SectionHeader'
import CommandField from '../shell/CommandField'
import CommandResults from '../shell/CommandResults'
import XpCard from '../profile/XpCard'
import ProfileDialog from '../profile/ProfileDialog'
import ModuleCard from './ModuleCard'
import ContinueRow from './ContinueRow'

const { copy } = knobs
const NAME = 'home'
const OTHERS = LISTED.filter((tab) => tab.id !== 'home')

// The newest place per tab, newest first, leaving out Home itself.
function recentPlaces(steps) {
  const seen = new Set(['home'])
  const places = []
  for (const step of [...steps].reverse()) {
    if (seen.has(step.tab) || !step.value) continue
    seen.add(step.tab)
    places.push(step)
  }
  return places.slice(0, knobs['continue-max'])
}

export default function HomePanel({ accent, onGo }) {
  const [name] = useState(getProfile)
  const [asking, setAsking] = useState(false)
  const overview = useQuery({ queryKey: ['overview', name], queryFn: fetchOverview, enabled: !!name, retry: false })
  const { rewards } = useRewards(name)
  const { steps } = useJourney()
  const line = useCommandLine(LISTED, (row) => onGo(row.tabId, row.value))
  const sums = progressByTab(overview.data?.modules)
  const streak = overview.data?.streak
  const showing = line.rows.length > 0

  return (
    <div className="panel space-y-6" style={{ '--c': accent }}>
      <SectionHeader title={copy.title} arabic={copy.arabic} subtitle={copy.subtitle} />

      <div className="cb" data-open="true" style={{ width: "100%", "--command-rest-w": "100%" }}>
        <CommandField line={line} name={NAME} placeholder={copy.placeholder} showing={showing} />
        {showing && (
          <CommandResults id={`${NAME}-results`} name={NAME} rows={line.rows} tabs={LISTED} colorOf={accentOf}
            active={line.active} onHover={line.setActive} onPick={line.run}
            railTab={line.rows[line.active]?.tabId} onRail={(id) => onGo(id)} />
        )}
      </div>

      <ContinueRow places={recentPlaces(steps)} title={copy.continue} onGo={onGo} />

      {name ? (
        <div className="grid grid-cols-2 gap-3">
          <XpCard rewards={rewards} />
          {streak > 0 && (
            <p className="col-span-2 type-small text-[var(--text-dim)]">
              {streak === 1 ? copy['streak-one'] : `${streak} ${copy['streak-many']}`}
            </p>
          )}
        </div>
      ) : (
        <button type="button" onClick={() => setAsking(true)} aria-haspopup="dialog"
          className="tap type-small px-3 rounded-[var(--radius-sm)] border border-[var(--border)] text-[var(--text-dim)] hover:text-[var(--text)]">
          {copy.guest}
        </button>
      )}
      {asking && <ProfileDialog onClose={() => setAsking(false)} />}

      {GROUPS.filter((group) => group.id !== 'start').map((group) => (
        <section key={group.id} className="space-y-2" aria-label={group.label}>
          <h3 className="type-small font-bold text-[var(--text-dim)]">{group.label}</h3>
          <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
            {OTHERS.filter((tab) => tab.group === group.id).map((tab) => (
              <ModuleCard key={tab.id} tab={tab} accent={accentOf(tab.id)} progress={sums[tab.id]} onOpen={onGo} />
            ))}
          </div>
        </section>
      ))}
    </div>
  )
}
