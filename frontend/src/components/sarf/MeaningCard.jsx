import RootActions from '../ui/RootActions'
import ShowRest from '../ui/ShowRest'
import { Skeleton } from '../ui/Skeleton'

/**
 * What the word means, and the two ways out of this tab.
 *
 * The buttons used to sit in a line of their own under the cards, with the root
 * repeated beside them: a row that said nothing the ROOT card did not, in the
 * one place a reader has finished reading. They live here now, under the
 * meaning, where the next question actually is, where does this word come from
 * and where is it used.
 *
 * The meaning itself is the dictionary's first sense. Define is for the reader
 * who wants the rest of that entry, so the card is the short answer and the
 * button is the long one.
 */
export default function MeaningCard({ meaning, pending, root, onGo, accent, i }) {
  return (
    <div
      dir="ltr"
      style={{ '--i': i, '--c': accent }}
      className="card rise-in flex flex-col gap-2"
    >
      <div className="eyebrow">Meaning</div>

      {/* Three lines, then the rest one press away. Half the dictionary's senses
          are a handful of words, but the longest is 800 characters of prose about
          the letter hamzah. Cut with ShowRest, as everywhere else: a hover title
          said nothing on a phone, where there is no hover. */}
      {meaning && (
        <ShowRest lines={3} accent={accent} className="type-body text-[var(--text)]">{meaning}</ShowRest>
      )}
      {!meaning && pending && <Skeleton className="h-4 w-2/3" />}
      {/* A gap stays a gap. The dictionary has no entry for plenty of real
          words, and Define is exactly the button for that case. */}
      {!meaning && !pending && (
        <div className="type-small text-[var(--text-faint)]">No dictionary entry for this word.</div>
      )}

      {root && (
        <RootActions
          root={root}
          onGo={onGo}
          exclude="sarf"
          showRoot={false}
          className="mt-auto pt-1"
        />
      )}
    </div>
  )
}
