/**
 * Home: where the app opens. One thing to carry on with, and every tab under
 * its group, all in view. The level lives behind the header's profile button,
 * not here.
 *
 * Where you stopped comes from the journey (lib/nav/journey.js), never a list
 * written here; with no history, the first fixed tab (lib/nav/tabs.js) stands in. The progress under each card is the overview the profile reads,
 * filed to tabs by lib/nav/moduleTab.js. The line is the header's own command line.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { overviewQuery } from '../../lib/learner/record'
import { getProfile } from '../../lib/learner/profile'
import { useHealth } from '../../lib/api/useHealth'
import { resumePlace, useJourney } from '../../lib/nav/journey'
import { progressByTab } from '../../lib/nav/moduleTab'
import { useCommandLine } from '../../lib/nav/useCommandLine'
import { accentOf, FIXED, GROUPS, HOME, LISTED, START } from '../../lib/nav/tabs'
import { progressText } from '../../lib/shell/homeCopy'
import { copy as offlineCopy, noSignal } from '../../lib/shell/offline'
import knobs from '../../config/home.json'
import { useMedia, PHONE } from '../../lib/hooks/useMedia'

import ArabicText from '../ui/ArabicText'
import ErrorAlert from '../ui/ErrorAlert'
import TabGroups from '../ui/TabGroups'
import CommandField from '../shell/CommandField'
import CommandResults from '../shell/CommandResults'
import LogInButton from '../profile/LogInButton'
import LevelPicker from '../level/LevelPicker'
import ModuleCard from './ModuleCard'
import ResumeCard from './ResumeCard'
import StatsButton from './StatsButton'
import StatsRail from './StatsRail'

const { copy } = knobs
const NAME = 'home'
const OTHERS = LISTED.filter((tab) => tab.id !== HOME)
const FALLBACK = FIXED.filter((id) => id !== HOME)
const tabOf = (id) => LISTED.find((tab) => tab.id === id)
const SHOWN_GROUPS = GROUPS.filter((group) => group.id !== START && OTHERS.some((tab) => tab.group === group.id))

export default function HomePanel({ accent, onGo }) {
  const phone = useMedia(PHONE)
  const [name] = useState(getProfile)
  const overview = useQuery(overviewQuery(name))
  const { steps } = useJourney()
  const health = useHealth()
  const line = useCommandLine(LISTED, (row) => onGo(row.tabId, row.value))
  const sums = progressByTab(overview.data?.modules)
  const showing = line.rows.length > 0
  const offline = health.status === 'error'
  // No signal is the phone's, not the server's: say so, and that what is saved still opens.
  const down = noSignal() ? offlineCopy : copy

  const resume = resumePlace(steps, LISTED, HOME)
  const first = !resume
  const lead = tabOf(resume?.tab ?? FALLBACK[0])
  const card = (tab, at) => (
    <ModuleCard key={tab.id} tab={tab} accent={accentOf(tab.id)} index={at} progressText={progressText(sums[tab.id])} onOpen={onGo} />
  )

  return (
    <div className="panel isolate space-y-6" style={{ '--c': accent }}>
      <header className="space-y-2">
        <div className="flex items-start justify-between gap-3">
          <h2 className="type-head rise-in text-3xl sm:text-5xl font-semibold leading-tight">
            {first ? copy['title-first'] : copy['title-resume']}
          </h2>
          {/* A wide screen has the column beside the tiles; a narrower one, this way into the same figures. */}
          <span className="lg:hidden"><StatsButton /></span>
        </div>
      </header>

      {offline && (
        <ErrorAlert title={down['offline-title']} onRetry={health.retryHealth}>{down['offline-body']}</ErrorAlert>
      )}

      {/* Beside the tiles on a wide screen, the progress column, held in view as the page scrolls. */}
      <div className="lg:grid lg:grid-cols-[minmax(0,1fr)_var(--layout-rail)] lg:gap-8 lg:items-start">
        <div className="space-y-6">
          <div className="cb" data-wide>
            <CommandField line={line} name={NAME} placeholder={phone ? copy['placeholder-phone'] : copy.placeholder} showing={showing} />
            {showing && (
              <CommandResults id={`${NAME}-results`} name={NAME} rows={line.rows} tabs={LISTED} colorOf={accentOf}
                active={line.active} onHover={line.setActive} onPick={line.run}
                railTab={line.rows[line.active]?.tabId} onRail={(id) => onGo(id)} />
            )}
          </div>

          {/* The quiet word sits in the room beside the card and scrolls with the page. */}
          <div className="md:flex md:items-center md:gap-6">
            <div className="space-y-4 md:max-w-2xl md:flex-[3] min-w-0">
              {/* A first visit asks how much Arabic you know, and starts there; after that, where you stopped. */}
              {first
                ? <LevelPicker copy={copy} onGo={onGo} />
                : <ResumeCard tab={lead} accent={accentOf(lead.id)} value={resume.value} label={copy['resume-label']} goLabel={copy['resume-go']}
                  progressText={progressText(sums[lead.id])} onGo={onGo} />}
              {!name && (
                <p className="flex lg:hidden flex-wrap items-center gap-x-3 gap-y-2 text-[var(--text-dim)]">
                  <span>{copy.guest}</span>
                  <LogInButton>{copy['guest-go']}</LogInButton>
                </p>
              )}
            </div>
            <div aria-hidden="true" className="hidden md:flex flex-1 justify-center min-w-0">
              <ArabicText className="outline-text [--outline-size:6rem] leading-none select-none">فهم</ArabicText>
            </div>
          </div>

          <section className="space-y-4" aria-labelledby="home-all">
            <h3 id="home-all" className="type-head text-xl font-semibold">{copy.all}</h3>
            {/* One goal to a row: its one-word name over its tiles. */}
            <div className="space-y-5">
              <TabGroups groups={SHOWN_GROUPS} tabs={OTHERS} heading="h4"
                grid="gap-2 sm:gap-3 grid-cols-3 sm:grid-cols-[repeat(auto-fill,minmax(8.5rem,1fr))] lg:grid-cols-4">
                {card}
              </TabGroups>
            </div>
          </section>
        </div>
        <div className="hidden lg:block sticky top-[calc(var(--app-header-h,0px)+var(--spacing)*5)]">
          <StatsRail name={name} />
        </div>
      </div>
    </div>
  )
}
