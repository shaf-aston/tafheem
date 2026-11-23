/**
 * The page reader's word bar: the word last pointed at or tapped, held at the foot of the screen.
 *
 * Its English large, the word it comes from and its role beside it, and a Look up
 * button big enough for a thumb. It stays put while the eye goes back to the
 * line, so a reader can point, read, and decide, and the mouse never has to cross
 * a gap to reach the button. Held above the phone's tab bar by .reader-dock, as
 * the Qur'an's recitation bar is.
 */
import ArabicText from '../ui/text/ArabicText'

export default function PageWordBar({ word, accent, onLookup }) {
  const lemma = word?.lemma && word.lemma !== word.arabic ? word.lemma : ''
  const role = word?.role || word?.pos
  return (
    <div
      style={{ '--c': accent }}
      className="reader-dock flex items-center gap-3 min-h-16 px-4 py-2 rounded-[var(--radius-lg)]
        border border-[var(--border-hi)] bg-[var(--surface-hi)] shadow-[var(--shadow-pop)]"
    >
      {word ? (
        <>
          <ArabicText size="lg" className="text-[var(--c)] shrink-0">{word.arabic}</ArabicText>
          <div className="flex flex-col min-w-0 flex-1">
            <span className="type-body text-[var(--text)] leading-snug" lang="en">{word.english || 'No English for this word'}</span>
            {(lemma || role) && (
              <span className="flex items-baseline gap-2 type-small text-[var(--text-dim)] min-w-0">
                {lemma && <span>from <ArabicText size="sm">{lemma}</ArabicText></span>}
                {role && <span className="truncate">{role}</span>}
              </span>
            )}
          </div>
          {onLookup && (
            <button
              type="button"
              onClick={() => onLookup(word.base || word.arabic)}
              className="shrink-0 min-h-[calc(var(--layout-tap-min)*1px)] px-4 rounded-[var(--radius-md)] type-ui font-medium
                bg-[var(--c)] text-[var(--on-accent)] hover:brightness-110"
            >
              Look up
            </button>
          )}
        </>
      ) : (
        <p className="type-small text-[var(--text-dim)]">Point at a word, or tap it, to see its meaning here.</p>
      )}
    </div>
  )
}
