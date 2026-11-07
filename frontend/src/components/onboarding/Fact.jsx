/** The one true fact shown after a pick: a big figure, a line under it, and where the figure comes from (a short screen drops the source, styles/growWorlds.css). */
export default function Fact({ fact }) {
  return (
    <aside className="grow-teach-note space-y-1 rise-in" aria-live="polite">
      <p className="type-title font-semibold" dir="auto">{fact.stat}</p>
      <p className="onb-fact-body">{fact.body}</p>
      {fact.source && <p className="onb-fact-source type-small text-[var(--text-faint)]">{fact.source}</p>}
    </aside>
  )
}
