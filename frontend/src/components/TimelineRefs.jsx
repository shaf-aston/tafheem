/**
 * The row of flags and references under anything on a timeline.
 *
 * Its own component because an event and a step inside it say where they are
 * told in exactly the same words, and two copies of this row would drift: the
 * amber dot that means "nothing here checks this number" is the kind of thing
 * that gets fixed in one place and missed in the other.
 *
 * Every reference is a way out of this tab rather than a line of text. A Qur'an
 * reference opens the Qur'an tab at its first ayah, because that tab reads one
 * ayah at a time. A hadith reference opens the collection where its number was
 * checked, named in the data as `checked` with the link shape in library.json.
 *
 * A hadith number with no `checked` on it keeps the amber dot and says so: no
 * hadith collection is installed here, so the app itself can confirm nothing,
 * and an unchecked number must not look like a checked one.
 */
import Chip from './ui/Chip'
import { firstAyah } from '../lib/timelineLayout'

const refKey = (ref, i) => `${ref.quran ?? ref.hadith ?? ref.book}-${ref.number ?? i}`

export default function TimelineRefs({ flags = [], refs = [], library, accent, onGo, className = '' }) {
  if (!flags.length && !refs.length) return null

  return (
    <div className={`flex flex-wrap items-center gap-1.5 ${className}`.trim()}>
      {flags.map((flag) => (
        <Chip key={flag} cite accent="var(--warn)">{library.flags[flag]}</Chip>
      ))}
      {refs.map((ref, i) => (
        ref.quran
          ? (
            <Chip cite
              key={refKey(ref, i)}
              accent={accent}
              onClick={() => onGo?.('quran', firstAyah(ref.quran))}
              title={`Open the Qur'an at ${firstAyah(ref.quran)}`}
            >
              Qur'an {ref.quran}
            </Chip>
          )
          : (() => {
            const source = library.collections[ref.hadith ?? ref.book]
            const checked = ref.hadith && ref.checked
            // sunnah.com letters the narrations that share one number, and the
            // letter belongs to the reference: 157 and 157c are two hadiths.
            const number = `${ref.number}${ref.part ?? ''}`
            return (
              <Chip cite
                key={refKey(ref, i)}
                accent={ref.hadith && !checked ? 'var(--warn)' : accent}
                href={checked ? source.cite.replace('{number}', number) : undefined}
                title={
                  checked ? `Read it on ${new URL(source.cite).host}`
                    : ref.hadith ? 'The number is as commonly cited; nothing here checks it'
                      : undefined
                }
              >
                {/* An unchecked number wears the warning colour on its dot and
                    says so in words, so colour is never the only signal. */}
                {source.name}
                {ref.hadith ? ` ${number}${checked ? '' : ' · number not checked'}` : ''}
              </Chip>
            )
          })()
      ))}
    </div>
  )
}
