import { useCallback, useEffect, useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { TABS, accentOf } from './lib/tabs'
import { lastPlaceOn, onJump, startJourney, startOver, visit } from './lib/journey'
import { useTabShortcuts } from './lib/useTabShortcuts'
import { useHealth } from './lib/useHealth'
import { moodFrom } from './lib/mood'

import CursorLight from './components/CursorLight'
import CommandBar from './components/ui/CommandBar'
import ErrorAlert from './components/ui/ErrorAlert'
import Mascot from './components/ui/Mascot'
import SettingsPanel from './components/ui/SettingsPanel'
import SpatialHome from './components/ui/SpatialHome'
import SourceFooter from './components/ui/SourceFooter'
import TabStrip from './components/ui/TabStrip'
import ArabicText from './components/ui/ArabicText'

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: 1 } } })

// Nothing to say about a round: no streak, no answer just given.
const QUIET = { streak: 0, answer: null }

// Numbers the arrivals. A panel cannot tell "this word has come again" from
// "this word never left" by the word alone: its own searches are steps on the
// journey too, so the back arrow can land on the word already in its box. The
// number is what says an arrival happened. It must never repeat, which a clock
// can: two arrivals can share a millisecond.
let arrivals = 0

const STATUS = {
  checking: { color: 'var(--tab-dict)',  label: 'Connecting…', pulse: true },
  ok:       { color: 'var(--success)',   label: 'Backend Ready' },
  error:    { color: 'var(--danger)',    label: 'Backend offline' },
}

function StatusPill({ status, nlpEngine, aiBackend, ear }) {
  const { color, label, pulse } = STATUS[status]

  // Engine names are for whoever runs the thing, not for whoever reads Arabic
  // with it. The dot and three words say whether it is up; the names stay in
  // the tooltip for anyone who wants them.
  const engines = [nlpEngine, aiBackend, ear].filter(Boolean).join(' + ')

  return (
    <div
      className="flex items-center gap-2 type-small text-[var(--text-dim)]"
      aria-live="polite"
      title={engines ? `Engines: ${engines}` : undefined}
    >
      <span
        className={`w-2 h-2 rounded-full shrink-0 ${pulse ? 'animate-pulse' : ''}`}
        style={{ background: color, boxShadow: `0 0 8px ${color}` }}
      />
      {/* Dot only on a phone: the full label plus the command bar and gear
          overflows a 375px screen and scrolls the whole page sideways. */}
      <span className="sr-only sm:not-sr-only">{label}</span>
    </div>
  )
}

function AppContent() {
  // Where the journey lands: the address if it names a word, else the tab's
  // last word from the saved path. Started here, before the first render, so
  // the panel is born on that word rather than remounted onto it.
  const [opened] = useState(() => startJourney(TABS) ?? { tab: TABS[0].id, value: null })
  const [activeTab, setActiveTab] = useState(opened.tab)
  const [bannerDismissed, setBannerDismissed] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [spatialOpen, setSpatialOpen] = useState(false)
  // A root handed from one tab to another. Held here because it is the only
  // thing the panels share; each one reads it once and then owns its own state.
  const [handoff, setHandoff] = useState(
    opened.value ? { tab: opened.tab, value: opened.value, at: 0 } : null,
  )
  const { status, nlpEngine, aiBackend, ear } = useHealth()
  // Dismissing hides this outage only. Once the backend is back, the next drop
  // is news again; before this, one click silenced every later outage too.
  useEffect(() => {
    if (status === 'ok') setBannerDismissed(false)
  }, [status])

  const active = TABS.find((t) => t.id === activeTab) ?? TABS[0]
  const ActiveTab = active.Component

  // The practice tabs (Quiz, Tamreen) say how it is going.
  // They report; `moodFrom` below is still the only thing that decides.
  const [quiz, setQuiz] = useState(QUIET)
  const accent = accentOf(activeTab)

  // A tab chosen with nothing in hand opens on the word it was last on, from
  // the journey, so glancing at another tab and coming back costs nothing.
  // Already there (the active tab clicked again): not a step, and the panel
  // is left exactly as it is.
  const switchTab = useCallback((id, handed = null) => {
    const incoming = handed ?? lastPlaceOn(id)
    if (!visit(id, incoming)) return
    setActiveTab(id)
    // Leaving the quiz ends the round as far as the pen is concerned, a streak
    // face still on while reading the Qur'an is describing nothing.
    setQuiz(QUIET)
    setHandoff(incoming ? { tab: id, value: incoming, at: ++arrivals } : null)
  }, [])

  useTabShortcuts(TABS, switchTab)

  // The trail and the browser's back arrow are the same list; this follows the
  // arrow: a step returned to is handed back to its panel exactly like a
  // hand-off, which is what makes it load that word again.
  useEffect(() => {
    return onJump((step) => {
      setActiveTab(step.tab)
      setQuiz(QUIET)
      setHandoff(step.value ? { tab: step.tab, value: step.value, at: ++arrivals } : null)
    })
  }, [])

  // Panels report where they got to; which tab that is, is App's to know.
  const recordVisit = useCallback((value) => visit(activeTab, value), [activeTab])

  // The header is pinned, so anything else pinned sits under it: its height is
  // published as --app-header-h, kept true as it wraps on a narrow screen.
  const pinHeader = useCallback((node) => {
    if (!node) return
    const root = document.documentElement
    new ResizeObserver(() => root.style.setProperty('--app-header-h', `${node.offsetHeight}px`)).observe(node)
  }, [])

  return (
    <div className="min-h-screen" style={{ '--c': accent }}>
      <header ref={pinHeader} className="app-header sticky top-0 z-40">
        <div className="shell py-1 flex items-center justify-between gap-3">
          {/* The name used to be printed here in two lines that said what every
              tab below already says. The pen is the name now, and clicking it
              opens the launcher, so the corner went from a caption to a way
              out to everything. The heading itself stays for a screen reader,
              which has no picture to read. */}
          <h1 className="sr-only">Tafheem: Nahw and Sarf, Arabic grammar word by word, with the reason</h1>
          <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => setSpatialOpen(true)}
            title="Everything, at once"
            aria-label="Open the launcher"
            aria-haspopup="dialog"
            className="icon-button pen-badge"
          >
            {/* The pen says what the app is doing: waiting, working, or unable to
                reach the backend. It reads the health check, holds no state. */}
            <Mascot
              mood={moodFrom({
                offline: status === 'error',
                busy: status === 'checking',
                ...quiz,
              })}
            />
          </button>
          {/* One click, no arming: it forgets where you have been and the
              saved answers, and reopens this tab clean. The wipe with
              real cost, settings and streak, stays two clicks deep in Settings. */}
          <button
            type="button"
            onClick={startOver}
            title="Start over"
            aria-label="Start over: forget where you have been and your answers, and reopen this tab clean"
            className="icon-button"
          >
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M3 12a9 9 0 1 0 3-6.7" />
              <path d="M3 4v5h5" />
            </svg>
          </button>
          </div>

          <div className="flex items-center gap-2 min-w-0">
            <CommandBar tabs={TABS} colorOf={accentOf} onGo={switchTab} />
            <StatusPill status={status} nlpEngine={nlpEngine} aiBackend={aiBackend} ear={ear} />
            <button
              type="button"
              onClick={() => setSettingsOpen(true)}
              title="Settings"
              aria-label="Settings"
              className="icon-button"
            >
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <circle cx="12" cy="12" r="3" />
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1.08-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6 1.65 1.65 0 0 0 10 3.09V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9c.14.35.4.64.73.82H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
              </svg>
            </button>
          </div>
        </div>

        <div className="shell">
          <TabStrip tabs={TABS} active={activeTab} colorOf={accentOf} onSelect={switchTab} />
        </div>
      </header>

      {status === 'error' && !bannerDismissed && (
        <div className="shell pt-4 relative">
          <ErrorAlert title="Backend offline">
            The backend is not running.
            {/* The command was the only advice here; most readers can't run
                it, so it moves behind a summary instead of leading. */}
            <details className="mt-2">
              <summary className="cursor-pointer">The command, if you run it yourself</summary>
              <code className="mt-1 block px-1 rounded bg-[var(--surface-hi)] text-[var(--text)]">
                python -m uvicorn backend.main:app --reload
              </code>
            </details>
          </ErrorAlert>
          <button
            type="button"
            aria-label="Dismiss backend warning"
            onClick={() => setBannerDismissed(true)}
            className="absolute top-6 right-6 w-7 h-7 grid place-items-center rounded-full border text-[var(--danger)] bg-[var(--surface)] hover:opacity-70 text-sm"
            style={{ borderColor: 'color-mix(in srgb, var(--danger) 50%, transparent)' }}
          >
            ✕
          </button>
        </div>
      )}

      {/* The tabpanel role sits on the inner element, not on <main>: overriding
          main's own role would leave the page with no main landmark to skip to. */}
      <main className="shell py-8">
        <div role="tabpanel" id="tabpanel" aria-labelledby={`tab-${activeTab}`}>
          {/* Keyed by the tab and nothing else. Remounting on tab change is
              what replays each panel's entrance animation; a word arriving on
              the tab already open is NOT a new panel, and it used to be keyed
              that way. Every back press then tore the whole column down, faded
              it in from nothing over 220ms and left the page collapsed to an
              empty panel's height while the word was fetched again, which read
              as the screen blinking. The panels follow the word themselves
              now; see each one's "a word arriving" block. */}
          <div key={activeTab} className={`fade-in${active.study ? ' study' : ''}`}>
            <ActiveTab
              accent={accent}
              incoming={handoff?.tab === activeTab ? handoff.value : null}
              arrival={handoff?.tab === activeTab ? handoff.at : null}
              onGo={switchTab}
              onVisit={recordVisit}
              onProgress={setQuiz}
            />
          </div>
        </div>
      </main>

      {/* The credits used to be one hardcoded line that named three sources and
          stayed the same on every tab, including tabs that read none of them.
          It now names what THIS tab is built on, read from data/sources.json;
          so a source added to a panel appears here without anyone remembering
          to come and edit a sentence. */}
      <footer className="border-t border-[var(--border)] mt-16 py-8 text-[var(--text-faint)]">
        {/* The same width as everything above it. It was held to a narrower
            column of its own, which is why a list of thirteen sources wrapped
            into a stripe while two thirds of the page sat empty beside it. */}
        <div className="shell space-y-5">
          <SourceFooter tab={activeTab} onSeeAll={() => setSettingsOpen(true)} />

          {/* The two lines that belong to the whole app rather than to this
              tab, under the list and centred, which is where a colophon goes. */}
          <div className="text-center space-y-2 pt-4 border-t border-[var(--border)]">
            <p className="type-small">
              {aiBackend && !aiBackend.startsWith('none')
                ? `Local NLP + ${aiBackend.split(' ')[0]}`
                : 'Local NLP, works offline'}
            </p>
            <ArabicText as="p">وَمَا تَوْفِيقِي إِلَّا بِاللَّهِ</ArabicText>
          </div>
        </div>
      </footer>
      <SettingsPanel open={settingsOpen} onClose={() => setSettingsOpen(false)} />
      <SpatialHome
        open={spatialOpen}
        onClose={() => setSpatialOpen(false)}
        tabs={TABS}
        colorOf={accentOf}
        onGo={switchTab}
        here={activeTab}
      />
      {/* Drawn last so it sits over the page, and once for the whole app. */}
      <CursorLight />
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  )
}
