/**
 * Every tab under its group's heading, as Home and the All sections menu both
 * show them. `children(tab)` draws one tab; `grid` sets the columns; `heading`
 * is the group title's level under the page's own headings.
 */
import { useId } from 'react'

export default function TabGroups({ groups, tabs, grid, heading: Heading = 'h3', children }) {
  const id = useId()
  return groups.map((group) => (
    <section key={group.id} className="space-y-2 pt-1" aria-labelledby={`${id}-${group.id}`}>
      <Heading id={`${id}-${group.id}`} className="type-small font-bold text-[var(--text-dim)]">{group.label}</Heading>
      <div className={`grid ${grid}`}>
        {tabs.filter((tab) => tab.group === group.id).map(children)}
      </div>
    </section>
  ))
}
