/**
 * Two or three words of English under an Arabic grammar term (lib/nahw/grammarTerms
 * roleGloss, caseGloss, posGloss): the term leads, this only says what it names.
 * Nothing for a term with no English, so a card never shows an empty line.
 */
export default function Gloss({ children, className = '' }) {
  if (!children) return null
  return <span lang="en" dir="ltr" className={`type-tiny text-[var(--text-faint)] ${className}`}>{children}</span>
}
