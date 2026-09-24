/**
 * A pill you tap to ask the same question about something else.
 *
 * The Recent searches and the root choices under the classical card are the same
 * control doing the same job, and were drifting into two slightly different
 * pills. One component, so a change to how a chip looks cannot land in one place
 * and miss the other.
 *
 * `selected` is for a row where one chip is the current choice, it sets
 * aria-pressed so a screen reader says which. A row of plain shortcuts, where
 * nothing is "on", leaves it undefined and no state is announced.
 *
 * `tinted` is the filter-row look: no surface behind it, and the chosen one
 * filled with its own accent rather than only outlined. The tarkeeb filters
 * had this as a second Chip of their own until it moved here.
 *
 * `quiet` is the Recent-searches look: a row of things already done, which sits
 * above the search box and should not compete with it. Fainter text, a fainter
 * edge, and a little tighter, so sixteen of them read as a margin note rather
 * than as sixteen buttons. Hovering brings a chip back to full strength.
 *
 * `href` makes the chip a link out of the app rather than a button. Same pill,
 * because a reference that opens sunnah.com and a reference that opens the
 * Qur'an tab are the same kind of thing to the reader.
 *
 * Every chip is the same height, from layout.chip, and its contents are centred
 * in it. A pill that grows to fit its own text is a different height in each
 * language, because Arabic is set on a taller rung than an English label and
 * carries a reading line-height on top of that. A Recent row with both in it
 * came out with the Arabic pills at twice the height of the English ones. So
 * the Arabic in a chip takes the smallest rung, the one meant for a name inside
 * a control beside English names, and the inline line-height rather than the
 * paragraph one, and then the height is pinned so nothing can drift again.
 */
import ArabicText from './ArabicText'

export default function Chip({
  children, onClick, accent, arabic = false, selected, title, tinted = false,
  quiet = false, cite = false, href,
}) {
  const Tag = href ? 'a' : 'button'
  // `cite` is a reference under a story: small, in its accent, with a dot, so a
  // row of sources reads as a footnote rather than a row of buttons.
  if (cite) {
    // Nothing to open (a caution, a printed book): plain text, not a dead button.
    const Cite = href ? 'a' : onClick ? 'button' : 'span'
    return (
      <Cite
        {...(href
          ? { href, target: '_blank', rel: 'noreferrer noopener' }
          : onClick ? { type: 'button', onClick } : null)}
        title={title}
        style={{
          borderColor: `color-mix(in srgb, ${accent} 45%, var(--border))`,
          color: `color-mix(in srgb, ${accent} 80%, var(--text))`,
        }}
        className="press type-tiny leading-none rounded-full inline-flex items-center gap-1.5 shrink-0 whitespace-nowrap
          px-2 py-1 border bg-[color-mix(in_srgb,var(--surface-hi)_70%,transparent)]
          hover:bg-[var(--surface-hi)] transition-colors"
      >
        <span className="w-[5px] h-[5px] rounded-full bg-current" aria-hidden="true" />
        {children}
      </Cite>
    )
  }
  return (
    <Tag
      {...(href
        ? { href, target: '_blank', rel: 'noreferrer noopener' }
        : { type: 'button', onClick })}
      title={title}
      aria-pressed={selected}
      style={{
        '--c': accent,
        ...(selected ? { borderColor: accent, color: accent } : null),
        ...(tinted && selected
          ? { background: `color-mix(in srgb, ${accent} 14%, transparent)` }
          : null),
      }}
      className={`press type-small leading-none rounded-full transition-colors
        inline-flex items-center justify-center shrink-0 whitespace-nowrap
        h-[var(--layout-chip)]
        hover:border-[var(--c)] hover:text-[var(--text)]
        ${quiet
          ? 'px-2 border border-[var(--border)] text-[var(--text-faint)] opacity-75 hover:opacity-100'
          : 'px-2.5 border border-[var(--border)] text-[var(--text-dim)]'}
        ${tinted ? 'bg-transparent' : 'bg-[var(--surface)]'}`}
    >
      {arabic
        ? <ArabicText size="tiny" className="arabic-inline">{children}</ArabicText>
        : children}
    </Tag>
  )
}
