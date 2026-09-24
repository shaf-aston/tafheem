/**
 * Panel title, plus the one line that says what this panel is for.
 *
 * The way back rides on the end of the title line rather than on a line of its
 * own: it is needed on every panel and it is worth no vertical space.
 *
 * `aside` is for a panel's own control, Nahw's two views, riding there too. A
 * short title leaves that half of the line empty, and a control put under the
 * title instead pushed the whole panel down a row for no gain.
 */
import ArabicText from './ArabicText'
import Trail from './Trail'

export default function SectionHeader({ title, arabic, subtitle, aside = null }) {
  return (
    <div className="fade-in">
      <div className="flex items-baseline justify-between gap-4 flex-wrap">
        <div className="flex items-baseline gap-2 flex-wrap">
          {/* No leading at all on the title, so the line box holds the letters
              and nothing else. A title and the sentence explaining it are one
              thing, and the gap between them should be smaller than the gap to
              whatever comes next, most of what used to sit there was empty line
              box, not margin. */}
          <h2 className="text-xl font-semibold leading-none text-[var(--text)]">{title}</h2>
          {arabic && (
            /* arabic-inline, not the reading line-height: the tall empty line
               box under one word was most of the gap beneath this header. */
            <ArabicText className="arabic-inline text-[var(--text-faint)]">
              {arabic}
            </ArabicText>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 flex-wrap min-w-0 ms-auto">
          {aside}
          <Trail />
        </div>
      </div>
      {subtitle && <p className="text-[var(--text-dim)] text-sm leading-snug mt-1 max-w-prose">{subtitle}</p>}
    </div>
  )
}
