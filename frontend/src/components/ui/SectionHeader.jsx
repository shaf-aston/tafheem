/**
 * Panel title, plus the one line that says what this panel is for.
 *
 * The way back rides on the end of the title line rather than on a line of its
 * own: it is needed on every panel and it is worth no vertical space.
 *
 * `aside` is for a panel's own control, Nahw's two views, riding there too. A
 * short title leaves that half of the line empty, and a control put under the
 * title instead pushed the whole panel down a row for no gain.
 *
 * `nameOf` turns a step's address into words, for a tab whose addresses are ids.
 * `history={false}` drops the trail, for a panel that draws its own way back
 * (Colloquial's course trail): two trails stacked read as one path said twice.
 *
 * `answered`: something has been looked up, so on a phone the line saying what
 * the panel is for gives its room to the answer, which it was pushing under the
 * bottom bar.
 *
 * `tab` is the tab's id: its name, Arabic name and emblem then come from the
 * registry (lib/nav/tabs.js), the one place they are written, so renaming a tab is
 * one edit. `title`, `arabic` and `emblem` passed as well win, for a panel that
 * names a step rather than itself.
 */
import ArabicText from './ArabicText'
import Emblem from './Emblem'
import Trail from './Trail'
import { TABS } from '../../lib/nav/tabs'

export default function SectionHeader({ tab, title, arabic, subtitle, emblem, aside = null, nameOf, history = true, answered = false }) {
  const named = tab ? TABS.find((t) => t.id === tab) : null
  title ??= named?.label
  arabic ??= named?.arabic
  emblem ??= named?.emblem
  return (
    <div>
      <div className="flex items-baseline justify-between gap-4 flex-wrap">
        {/* The picture centres on the title; the two names keep one baseline between them. */}
        <div className="flex items-center gap-2.5 min-w-0">
          {emblem && <Emblem id={emblem} className="section-emblem" />}
          <div className="flex items-baseline gap-2 flex-wrap min-w-0">
          {/* No leading at all on the title, so the line box holds the letters
              and nothing else. A title and the sentence explaining it are one
              thing, and the gap between them should be smaller than the gap to
              whatever comes next, most of what used to sit there was empty line
              box, not margin. */}
          <h2 className="type-head text-xl md:text-3xl font-semibold leading-none text-[var(--text)]">{title}</h2>
          {arabic && (
            /* arabic-inline, not the reading line-height: the tall empty line
               box under one word was most of the gap beneath this header. */
            <ArabicText className="arabic-inline section-title-ar text-[var(--text-faint)]">
              {arabic}
            </ArabicText>
          )}
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 flex-wrap min-w-0 ms-auto">
          {aside}
          {history && <Trail nameOf={nameOf} />}
        </div>
      </div>
      {subtitle && <p className={`text-[var(--text-dim)] text-sm leading-snug mt-1 ${answered ? 'max-sm:hidden' : ''}`}>{subtitle}</p>}
    </div>
  )
}
