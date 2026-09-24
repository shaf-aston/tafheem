/**
 * What the tab you are looking at is built on, at the foot of the page.
 *
 * A badge beside one answer says where that answer came from. This says where
 * the whole tab's answers come from, so a reader who never presses anything
 * still learns what the page rests on, and can follow it to the thing itself.
 *
 * Only sources this tab actually reads are listed, and which those are is
 * declared in data/sources.json, not decided here. A tab that gains a source
 * gains a line at its foot on its own.
 *
 * Deliberately quiet: this is the last thing on the page, not a warning. What
 * it must never do is go missing silently, a page that cannot say what it is
 * built on says that, rather than showing an empty line that reads as "nothing
 * to declare".
 *
 * A list, laid out in columns, rather than a paragraph. It was a centred run of
 * underlined names strung on middots, which wrapped mid-list and made thirteen
 * quiet credits into one loud stripe: every name underlined, no two lines
 * starting in the same place, and the page's whole width unused beside it. Now
 * each source is its own item in a column grid that fills the width available,
 * and the underline waits for the pointer. The dot in front carries how far the
 * source can be trusted, in the same colours the badges beside answers use, so
 * the list says something a run of names could not.
 */
import { levelOf } from '../../lib/confidence'
import { sourcesFor, useSources } from '../../lib/useSources'

export default function SourceFooter({ tab, onSeeAll }) {
  const { sources, isPending, isError } = useSources()

  // Nothing yet, and nothing worth a placeholder for: the page above is the
  // answer, and this line arriving a moment later costs the reader nothing.
  if (isPending) return null

  if (isError) {
    return (
      <p className="type-small text-[var(--text-faint)]">
        Couldn&rsquo;t reach the backend to say what this tab is built on.
      </p>
    )
  }

  const used = sourcesFor(sources, tab)

  // A tab that reads nothing is a mistake in sources.json, not a tab with
  // nothing behind it. Say so rather than printing an empty line.
  if (used.length === 0) {
    return (
      <p className="type-small text-[var(--text-faint)]">
        No sources are declared for this tab.
      </p>
    )
  }

  return (
    // As many columns as the width allows, each at least this wide. No
    // breakpoints to keep in step with anything: one narrow column on a phone,
    // four or five across a laptop, and the same rule decides both.
    //
    // The word References and the see-all link are cells of that same grid
    // rather than a row above it. They used to hold a line of their own with
    // the width of the page empty between them, which is a lot of quiet for a
    // credit; now they are the first and last things in one block that ends the
    // page.
    <ul className="grid gap-x-6 gap-y-1 [grid-template-columns:repeat(auto-fill,minmax(11rem,1fr))]">
      <li className="min-w-0">
        <h2 className="type-micro uppercase tracking-[0.14em] text-[var(--text-faint)] leading-relaxed">
          References
        </h2>
      </li>

      {used.map((source) => (
        <li key={source.key} className="min-w-0">
          <Source source={source} />
        </li>
      ))}

      {onSeeAll && (
        <li className="min-w-0">
          <button
            type="button"
            onClick={onSeeAll}
            className="type-small text-[var(--text-faint)] hover:text-[var(--text)]
              underline underline-offset-2 decoration-[var(--border-hi)] transition-colors
              leading-relaxed"
          >
            See all {sources.length}
          </button>
        </li>
      )}
    </ul>
  )
}

/**
 * One source. A link where there is something public to link to, plain text
 * where there is not, a printed book and a model running on this machine have
 * no address, and inventing one would be the opposite of the point.
 *
 * The confidence wording rides along in the tooltip so the difference between a
 * hand-checked corpus and a machine's guess is available here too, without
 * putting thirteen coloured badges across the bottom of every page.
 */
function Source({ source }) {
  const level = levelOf(source)
  const title = `${level.say} · ${source.where || source.detail}`
  const inside = (
    <>
      <span
        aria-hidden="true"
        className="shrink-0 w-1.5 h-1.5 rounded-full"
        style={{ background: level.color, opacity: 0.75 }}
      />
      <span className="truncate">{source.label}</span>
    </>
  )
  const row = 'type-small flex items-center gap-2 leading-relaxed'

  if (!source.url) {
    return <span title={title} className={`${row} text-[var(--text-faint)]`}>{inside}</span>
  }

  return (
    <a
      href={source.url}
      target="_blank"
      rel="noreferrer noopener"
      title={title}
      className={`${row} text-[var(--text-faint)] hover:text-[var(--text)]
        hover:underline underline-offset-2 transition-colors`}
    >
      {inside}
    </a>
  )
}
