/**
 * Every tab under its group's heading, as Home and the All sections menu both
 * show them, a group's `note` under its name. `children(tab, at)` draws one tab;
 * `grid` sets the columns, `className` each group's own layout; `heading`
 * is the group title's level under the page's own headings.
 */
import { useId } from 'react'

export default function TabGroups({ groups, tabs, grid, className = 'space-y-2', heading: Heading = 'h3', children }) {
  const id = useId()
  return groups.map((group) => (
    <section key={group.id} className={`pt-1 ${className}`} aria-labelledby={`${id}-${group.id}`}>
      <div className="flex flex-wrap content-start items-baseline gap-x-2">
        <Heading id={`${id}-${group.id}`} className="type-small font-bold text-[var(--text-dim)]">{group.label}</Heading>
        {group.note && <span className="type-small text-[var(--text-faint)]">{group.note}</span>}
      </div>
      <div className={`grid ${grid}`}>
        {tabs.filter((tab) => tab.group === group.id).map(children)}
      </div>
    </section>
  ))
}
