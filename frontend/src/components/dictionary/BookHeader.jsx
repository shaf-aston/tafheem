/**
 * The line that names a classical book over its entry: title, author and year,
 * then the switches and the source badge at the far edge.
 *
 * One header for every book on the shelf, Ibn Faris's card included. They each
 * had their own: Maqayees a badge alone, Lisan a title with the badge far off,
 * Lane a badge where the title goes, so moving between books read as moving
 * between apps. The badge stays the title only where it already is the title
 * (Lane), so one name is never printed twice.
 *
 * The year says its calendar: the Arabic books count from the Hijra and Lane
 * from his own, and a bare "d. 711" beside "d. 1876" read as one scale.
 */
import ArabicText from '../ui/text/ArabicText'
import SourceBadge from '../ui/feedback/SourceBadge'

const yearOf = (died, arabic) => (died ? `, d. ${died} ${arabic ? 'AH' : 'CE'}` : '')

export default function BookHeader({ title, author, died, arabic = true, source, children }) {
  const badgeIsTitle = title === source?.label
  return (
    <header className="flex items-center gap-x-2 gap-y-1.5 flex-wrap">
      {badgeIsTitle ? <SourceBadge source={source} /> : (arabic
        ? <ArabicText size="sm" className="font-medium text-[var(--text)]">{title}</ArabicText>
        : <span className="type-body font-medium text-[var(--text)]">{title}</span>)}
      <span className="type-small text-[var(--text-faint)]">
        {author}{yearOf(died, arabic)}
        {arabic ? '' : ' · in English'}
      </span>
      {/* In the header, not at the foot: under a long entry a badge at the
          bottom was a screen away from the name it vouches for. */}
      <div className="ms-auto flex items-center gap-2">
        {children}
        {!badgeIsTitle && source && <SourceBadge source={source} />}
      </div>
    </header>
  )
}
