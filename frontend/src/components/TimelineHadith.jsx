/**
 * The words of the hadiths an event is told by, under the event itself.
 *
 * A number and a link were all this tab gave: a reader who wanted to know what
 * the Prophet actually said had to leave the app for sunnah.com and find his
 * way back. The page has the room, so the words sit here, the book's Arabic and
 * the English under it, drawn by ui/HadithText: the same rendering the Hadith
 * tab's own browse and search use, since it is the same question, "what does
 * this hadith say", asked from a different door.
 *
 * The words come with the library (services/timelines), so an opened event has
 * them already. A cited number with no words is not an error: the tab shows the
 * number alone, as it always did. The chain of narrators is left to the Hadith
 * tab: here the reader came for what was said about the event.
 */
import HadithText from './ui/HadithText'
import { hadithKey } from '../lib/hadithWords'

export default function TimelineHadith({ refs = [], only, library, accent, className = '' }) {
  const told = refs
    .map((ref) => ({ ref, key: hadithKey(ref) }))
    // `only` is what this step is the first to cite (lib/hadithWords printedBy);
    // without it, everything cited here that has words.
    .filter(({ key }) => library.hadith?.[key] && (!only || only.has(key)))
  if (!told.length) return null

  return (
    <ul className={`list-none m-0 p-0 space-y-2 ${className}`.trim()}>
      {told.map(({ ref, key }) => (
        <HadithText
          key={key}
          label={`${library.collections[ref.hadith].name} ${ref.number}${ref.part ?? ''}`}
          arabic={library.hadith[key].arabic}
          english={library.hadith[key].english}
          accent={accent}
          hideChain
        />
      ))}
    </ul>
  )
}
