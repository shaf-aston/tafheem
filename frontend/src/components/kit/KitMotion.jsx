/**
 * The Kit's Motion page: every named move in the app, each on a card with the
 * class or file that owns it and a Replay. The moves are the real ones (the
 * classes in styles/motion.css and components.css, the ui/ pieces that wear
 * them), so a retune of a token shows here the moment it lands. Remounting is
 * what replays a one-shot move; the key is the whole trick.
 */
import { useState } from 'react'

import EmptyState from '../ui/feedback/EmptyState'
import Mascot from '../ui/display/Mascot'
import Odometer from '../ui/text/Odometer'
import SmallButton from '../ui/buttons/SmallButton'

const box = 'rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-hi)] px-4 py-3 type-small'

function Move({ title, owner, children }) {
  const [run, setRun] = useState(0)
  return (
    <section className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4 space-y-3 min-w-0">
      <header className="flex items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-[var(--text)]">{title}</h3>
          <p className="type-micro text-[var(--text-faint)] break-words">{owner}</p>
        </div>
        <SmallButton onClick={() => setRun((n) => n + 1)}>Replay</SmallButton>
      </header>
      <div key={run} className="min-h-16">{children}</div>
    </section>
  )
}

/** A number that changes on a press, to watch the odometer roll only the digits that move. */
function Rolling() {
  const [n, setN] = useState(1289)
  return (
    <div className="flex items-center gap-3">
      <span className="text-2xl font-bold"><Odometer value={n} /></span>
      <SmallButton onClick={() => setN((was) => was + 13)}>+13 XP</SmallButton>
    </div>
  )
}

export default function KitMotion() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <Move title="Arrive (uncover)" owner=".rise-in · motion.uncover-pct, arrive-from; .crisp turns the uncover off">
        <div className="flex flex-wrap gap-2">
          {[0, 1, 2].map((i) => <div key={i} className={`rise-in ${box}`} style={{ '--i': i }}>answer {i + 1}</div>)}
          <div className={`rise-in crisp ${box}`}>.crisp</div>
        </div>
      </Move>
      <Move title="A group arrives" owner=".dance · the dance group, motion.stagger-ms">
        <div className="flex flex-wrap gap-2">
          {[0, 1, 2, 3].map((i) => <div key={i} className={`dance ${box}`} style={{ '--i': i }}>.dance {i}</div>)}
        </div>
      </Move>
      <Move title="Hover lift" owner=".lift · motion.lift-px, the one lift every card shares">
        <div className={`lift ${box} w-fit`}>Point at me</div>
      </Move>
      <Move title="Twins differ" owner=".twin-same, .twin-diff · ui/text/TwinCards">
        <p dir="rtl" className="arabic text-xl flex gap-2">
          <span className="twin-same text-[var(--text-dim)]">إِنَّ</span>
          <span className="twin-diff" style={{ color: 'var(--danger)' }}>اللَّهَ</span>
          <span className="twin-same text-[var(--text-dim)]">غَفُورٌ</span>
        </p>
      </Move>
      <Move title="Nothing found" owner=".dots-gather · ui/feedback/EmptyState">
        <EmptyState>No entries.</EmptyState>
      </Move>
      <Move title="A number changes" owner=".odometer · ui/text/Odometer">
        <Rolling />
      </Move>
      <Move title="A sheet rises" owner="sheet-up · .phone-sheet on a phone, with the page softened (motion.soften-px)">
        <div className={box} style={{ animation: 'sheet-up calc(var(--motion-spring-ms) * 1ms) var(--motion-spring-ease) backwards' }}>
          A sheet
        </div>
      </Move>
      <Move title="Loading" owner=".skeleton · loop.shimmer-ms">
        <div className="skeleton h-10 w-40" aria-hidden="true" />
      </Move>
      <Move title="The qalam, idle" owner=".qalam · lib/motion/useLook: it leans and looks towards the mouse">
        <Mascot place="header" />
      </Move>
    </div>
  )
}
