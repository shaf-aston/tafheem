/**
 * One word of a reading line, with its English shown while it is pointed at.
 *
 * The English is handed to the page as data-gloss and drawn by index.css, never
 * written inside the word: text written inside it is text a reader selects, and
 * copying an ayah brought every word's English into the clipboard with it. The
 * meaning is still announced, as the word's description, so a screen reader
 * loses nothing.
 *
 * Both reading lines, one ayah studied and a whole surah read, are made of
 * these, so the two cannot drift into two ways of doing it.
 */
export default function GlossWord({ as: Tag = 'span', gloss, lit = false, className = '', children, ...props }) {
  return (
    <Tag
      className={`gloss-word${lit ? ' gloss-word-lit' : ''} ${className}`.trim()}
      data-gloss={gloss || undefined}
      aria-description={gloss || undefined}
      {...props}
    >
      {children}
    </Tag>
  )
}
