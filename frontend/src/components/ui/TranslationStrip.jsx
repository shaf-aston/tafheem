/**
 * The English at the foot of a card, joined to the Arabic above it.
 *
 * A translation set loose under a card reads as a different thing about the
 * same subject, not as the card speaking English: the reader has to work out
 * that the sentence below belongs to the text above. A hairline and a shade of
 * surface says it instead. Whoever translated it is credited inside the strip,
 * against the words they are answering for, rather than floating off to one
 * side where it looked like a second credit for the Arabic.
 *
 * Shared so the ayah view, the reading view and the reports of why an ayah came
 * down all say "and here it is in English" the same way.
 */
import SourceBadge from './SourceBadge'

export default function TranslationStrip({ source, pad = 'px-5 py-4', className = '', children }) {
  return (
    <div className={`${pad} border-t border-[var(--border)] bg-[var(--surface-hi)] ${className}`}>
      {children}

      {/* Pulled back by the badge's own padding so its text starts on the same
          line as the translation above it, not a step inside it. */}
      {source && (
        <div className="mt-2 -ml-2">
          <SourceBadge source={source} className="border-transparent px-2 py-0" />
        </div>
      )}
    </div>
  )
}
