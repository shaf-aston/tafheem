/**
 * One word of a reading line, its English shown on hover or focus. The English
 * rides in data-gloss and styles/components.css draws it, so copying the line copies only
 * the Arabic; aria-description still gives it to a screen reader. A learnt word
 * is underlined and says so.
 */
export default function GlossWord({ as: Tag = 'span', gloss, lit = false, learnt = false, children, ...props }) {
  const said = [gloss, learnt && 'learnt'].filter(Boolean).join(', ')
  return (
    <Tag
      className={['gloss-word', lit && 'gloss-word-lit', learnt && 'gloss-word-learnt'].filter(Boolean).join(' ')}
      data-gloss={gloss || undefined}
      title={learnt ? 'learnt' : undefined}
      aria-description={said || undefined}
      {...props}
    >
      {children}
    </Tag>
  )
}
