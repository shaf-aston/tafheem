/**
 * What the command line found, with the rail beside it.
 *
 * The rail is the seven tabs as their own letter, each in its own colour, and
 * it is the reason this is a component rather than a list inside the bar: the
 * orbit launcher shows the same rows the same way, and two copies of this would
 * have drifted apart the first time a group was renamed.
 *
 * It decides nothing. Rows come from lib/commandRoutes, colours from the theme,
 * and picking one is the caller's business.
 *
 * `name` prefixes the row ids. Focus stays in the caller's box while the arrows
 * walk this list, so the only way a screen reader can say which row is under
 * the cursor is for that box to point at the row by id. Two of these can be on
 * a page, so the prefix has to differ.
 */
import ArabicText from './ArabicText'
import { grouped, rowId } from '../../lib/commandRoutes'

export default function CommandResults({
  rows, tabs, colorOf, active = 0, onPick, onHover, onRail, railTab, id, name = 'cb',
}) {
  const blocks = grouped(rows)
  // Grouping reorders nothing, but the arrows count rows and the groups draw
  // them, so position in the original list is what says which one is lit.
  const positions = new Map(rows.map((row, i) => [row.key, i]))

  return (
    <div className="cb-results">
      {/* Not a tablist and not part of the listbox: it is a shortcut to a tab,
          the same journey the strip below the header already offers. */}
      <div className="cb-rail" aria-label="Jump to a tab">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            tabIndex={-1}
            title={tab.label}
            aria-label={tab.label}
            onMouseDown={(e) => { e.preventDefault(); onRail?.(tab.id) }}
            className="cb-rail-chip"
            data-lit={railTab === tab.id ? 'true' : undefined}
            style={{ '--c': colorOf(tab.id) }}
          >
            <ArabicText size="sm">{tab.mark}</ArabicText>
          </button>
        ))}
      </div>

      {/* A listbox may own only options and groups. The wrappers between it and
          the rows are marked presentational so the rows are really its own,
          otherwise a screen reader reads a plain list and never says which of
          how many a row is. */}
      <ul className="cb-rows" role="listbox" id={id} aria-label="Results">
        {blocks.map((block) => (
          <li key={block.group} role="group" aria-label={block.group}>
            <p className="cb-group" aria-hidden="true">{block.group}</p>
            <ul role="presentation">
              {block.rows.map((row) => {
                const index = positions.get(row.key)
                const accent = colorOf(row.tabId)
                return (
                  <li key={row.key} role="presentation">
                    <button
                      type="button"
                      role="option"
                      id={rowId(name, index)}
                      tabIndex={-1}
                      aria-selected={index === active}
                      data-active={index === active ? 'true' : undefined}
                      onMouseEnter={() => onHover?.(index)}
                      onMouseDown={(e) => { e.preventDefault(); onPick?.(row) }}
                      className="cb-row"
                      style={{ '--c': accent }}
                    >
                      <span className="cb-row-mark" aria-hidden="true">
                        <ArabicText size="sm">
                          {tabs.find((tab) => tab.id === row.tabId)?.mark}
                        </ArabicText>
                      </span>
                      <span className="cb-row-text">
                        {row.arabic
                          ? <ArabicText size="sm" className="cb-row-label">{row.label}</ArabicText>
                          : <span className="cb-row-label">{row.label}</span>}
                        {row.hint && <span className="cb-row-hint">{row.hint}</span>}
                      </span>
                    </button>
                  </li>
                )
              })}
            </ul>
          </li>
        ))}
      </ul>
    </div>
  )
}
