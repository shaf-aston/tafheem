/**
 * One word of a reading line, its English shown on hover or focus. The English
 * rides in data-gloss and index.css draws it, so copying the line copies only
 * the Arabic; aria-description still gives it to a screen reader.
 */
export default function GlossWord({ as: Tag = 'span', gloss, lit = false, children, ...props }) {
  return (
    <Tag
      className={lit ? 'gloss-word gloss-word-lit' : 'gloss-word'}
      data-gloss={gloss || undefined}
      aria-description={gloss || undefined}
      {...props}
    >
      {children}
    </Tag>
  )
}
