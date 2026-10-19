import { Activity, useCallback, useEffect, useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { FIXED, GROUPS, LISTED, TABS, accentOf } from './lib/tabs'
import { idle, inTurn } from './lib/warm'
import { useHealth } from './lib/useHealth'
import { moodFrom } from './lib/mood'
import { TOOLS } from './lib/tools'
import { useTabNavigation } from './lib/useTabNavigation'
import { useTools } from './lib/useTools'

import Backdrop from './components/shell/Backdrop'
import BackendBanner from './components/shell/BackendBanner'
import TabPane from './components/shell/TabPane'
import CursorLight from './components/shell/CursorLight'
import CommandBar from './components/shell/CommandBar'
import Mascot from './components/ui/Mascot'
import MapPanel from './components/shell/MapPanel'
import ProfileButton from './components/profile/ProfileButton'
import SettingsPanel from './components/shell/SettingsPanel'
import SpatialHome from './components/shell/SpatialHome'
import SourceFooter from './components/shell/SourceFooter'
import StatusPill from './components/shell/StatusPill'
import TabStrip from './components/shell/TabStrip'
import BottomNav from './components/shell/BottomNav'
import InstallBanner from './components/shell/InstallBanner'
import SectionsMenu from './components/shell/SectionsMenu'
import ArabicText from './components/ui/ArabicText'
import UndoToast from './components/ui/UndoToast'

const startOver = TOOLS.find((tool) => tool.id === 'startOver')

const queryClient = new QueryClient({
  // The data is fixed for the life of the backend: keep every answer, so a
  // second visit is instant and a fetch-ahead (lib/warm) is never repeated.
  defaultOptions: { queries: { retry: 1, staleTime: Infinity, gcTime: 30 * 60_000 } },
})

// Logs how long each tab's opening data took, `[open] hadith 212ms`; 0ms = already cached.
// The tab's code comes too (lib/tabs.js `panel`); a failed fetch is tried again on opening.
const openTab = (id) => {
  const tab = TABS.find((t) => t.id === id)
  const code = tab?.Component.preload?.().catch(() => {})
  const open = tab?.open
  if (!open) return code
  const at = performance.now()
  const data = Promise.resolve(open(queryClient)).then(() => console.debug(`[open] ${id} ${Math.round(performance.now() - at)}ms`))
  return Promise.all([code, data])
}

function AppContent() {
  const { activeTab, alive, handoffs, switchTab, said, round, strip, dock, placeInDock } = useTabNavigation()
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [mapOpen, setMapOpen] = useState(false)
  const [spatialOpen, setSpatialOpen] = useState(false)
  const [sectionsOpen, setSectionsOpen] = useState(false)
  const tools = useTools(TOOLS, { map: () => setMapOpen(true) })
  const { status, nlpEngine, aiBackend, ear } = useHealth()
  const accent = accentOf(activeTab)

  // Every tab's opening data, fetched once the page is idle, one tab at a time
  // so a tab pressed meanwhile is not queued behind all the others (lib/warm).
  useEffect(() => { idle(() => inTurn(TABS.map((t) => () => openTab(t.id)))) }, [])

  // The header is pinned, so anything else pinned sits under it: its height is
  // published as --app-header-h, kept true as it wraps on a narrow screen.
  const pinHeader = useCallback((node) => {
    if (!node) return
    const root = document.documentElement
    new ResizeObserver(() => root.style.setProperty('--app-header-h', `${node.offsetHeight}px`)).observe(node)
  }, [])

  return (
    <div className="min-h-screen bottom-nav-room" style={{ '--c': accent }}>
      {/* First child, so it paints under everything: its layer is below the page. */}
      <Backdrop />
      {/* First stop for a keyboard: past the header's controls to the panel. */}
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:start-2 focus:z-[var(--layer-tip)] focus:px-3 focus:py-2 focus:rounded-[var(--radius-sm)] focus:bg-[var(--surface)] type-ui">
        Skip to content
      </a>
      <header ref={pinHeader} className="app-header sticky top-0 z-[var(--layer-header)]">
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
                ...round,
              })}
            />
          </button>
          {/* Tools from lib/tools.js. Start over asks once (its `armed` look); the
              wipe with more cost, settings and streak, stays in Settings. */}
          {TOOLS.map(tools.now).map((tool) => (
            <button
              key={tool.id}
              type="button"
              onClick={tools.run[tool.id]}
              title={tool.label}
              aria-label={tool.aria}
              aria-haspopup={tool.dialog ? 'dialog' : undefined}
              className={`icon-button${tool.phone === 'more' ? ' phone-hide' : ''}${tools.armed === tool.id ? ' text-[var(--danger)] border-[var(--danger-edge)]' : ''}`}
            >
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                {tool.paths.map((d) => <path key={d} d={d} />)}
              </svg>
            </button>
          ))}
          <span className="sr-only" aria-live="polite">{tools.said}</span>
          </div>

          {/* Sits midway between the tools and the search, matching the colophon at the foot. */}
          <ArabicText as="p" className="phone-hide whitespace-nowrap">فَفِرُّوا إِلَى اللَّهِ</ArabicText>

          <div className="flex items-center gap-2 min-w-0">
            {/* Home has the command line and the tabs on a phone; the header keeps pen, profile, gear. */}
            <div className="phone-hide min-w-0"><CommandBar tabs={LISTED} colorOf={accentOf} onGo={switchTab} /></div>
            <span className="phone-hide"><StatusPill status={status} nlpEngine={nlpEngine} aiBackend={aiBackend} ear={ear} /></span>
            <ProfileButton />
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

        {/* Phones get the tabs at the bottom instead (BottomNav). */}
        <div className="shell hidden sm:block">
          <TabStrip tabs={strip} fixed={FIXED.length} active={activeTab} colorOf={accentOf} onSelect={switchTab} onAll={() => setSectionsOpen(true)} onHover={openTab} />
        </div>
      </header>

      <InstallBanner />

      <BackendBanner status={status} />

      {/* The tabpanel role sits on the inner element, not on <main>: overriding
          main's own role would leave the page with no main landmark to skip to. */}
      <main id="main" tabIndex={-1} className="shell py-8 glass rounded-[var(--radius-lg)] focus:outline-none">
        <div role="tabpanel" id="tabpanel" aria-labelledby={`tab-${activeTab}`}>
          {/* The last few tabs stay alive, hidden (React's Activity): a switch
              back shows the panel as it was, with no fetch, no fade and no
              cards rising again (TabPane). A switch used to tear the panel down
              and build it again, blank until its code and data came and then
              animated in. A word arriving on a tab is NOT a new panel: the
              panels follow the word themselves; see each one's "a word
              arriving" block. In TABS order, so a switch never moves a panel
              in the page and loses its scroll. */}
          {TABS.filter((tab) => alive.includes(tab.id)).map((tab) => (
            <Activity key={tab.id} mode={tab.id === activeTab ? 'visible' : 'hidden'}>
              <TabPane
                tab={tab}
                handoff={handoffs[tab.id]}
                accent={accentOf(tab.id)}
                onGo={switchTab}
                onVisit={said[tab.id].onVisit}
                onProgress={said[tab.id].onProgress}
              />
            </Activity>
          ))}
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

          {/* The colophon, on the same pane as the page and only as wide as its
              words, so the backdrop still shows around it. */}
          <div className="pt-4 border-t border-[var(--border)]">
            <div className="glass rounded-[var(--radius-lg)] w-fit mx-auto px-8 py-4">
              <ArabicText as="p">وَمَا تَوْفِيقِي إِلَّا بِاللَّهِ</ArabicText>
            </div>
          </div>
        </div>
      </footer>
      <UndoToast message={tools.undo.pending && startOver.pending.message} undoLabel={startOver.pending.undo} onUndo={tools.undo.cancel} />
      <SettingsPanel open={settingsOpen} onClose={() => setSettingsOpen(false)} />
      <MapPanel open={mapOpen} onClose={() => setMapOpen(false)} />
      <SpatialHome
        open={spatialOpen}
        onClose={() => setSpatialOpen(false)}
        tabs={LISTED}
        colorOf={accentOf}
        onGo={switchTab}
        here={activeTab}
      />
      <SectionsMenu
        open={sectionsOpen}
        onClose={() => setSectionsOpen(false)}
        onHover={openTab}
        groups={GROUPS}
        tabs={LISTED}
        colorOf={accentOf}
        onGo={switchTab}
        here={activeTab}
        dock={dock}
        onDock={placeInDock}
      >
        {/* The tools phones hide from the top bar, kept one tap inside More. */}
        <section className="sm:hidden space-y-2">
          <h3 className="type-small text-[var(--text-faint)]">Actions</h3>
          <div className="grid grid-cols-2 gap-2">
            {TOOLS.filter((tool) => tool.phone === 'more').map(tools.now).map((tool) => (
              <button
                key={tool.id}
                type="button"
                aria-haspopup={tool.dialog ? 'dialog' : undefined}
                aria-describedby={tool.hint ? `${tool.id}-hint` : undefined}
                onClick={() => { if (!tools.staysOpen(tool)) setSectionsOpen(false); tools.run[tool.id]() }}
                className={`tap min-h-11 rounded-[var(--radius-sm)] border type-body font-medium ${tool.danger ? 'border-[var(--danger-edge)] text-[var(--danger)]' : 'border-[var(--border)]'}`}
              >
                {tool.label}
              </button>
            ))}
          </div>
          {TOOLS.filter((tool) => tool.phone === 'more' && tool.hint).map((tool) => (
            <p key={tool.id} id={`${tool.id}-hint`} className="type-small text-[var(--text-faint)]">{tool.hint}</p>
          ))}
        </section>
      </SectionsMenu>
      <BottomNav tabs={LISTED} dock={dock} active={activeTab} colorOf={accentOf} onSelect={switchTab} onAll={() => setSectionsOpen(true)} onHover={openTab} />
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
