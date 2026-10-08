/**
 * What the narrator books say of one narrator, under his header: four groups
 * (his reliability, his habits in hadith, his life, and where our hadith
 * name him), each line with the book it comes from as a ui/SourceBadge and, where
 * the book has words for it, a snippet of them with "Show the rest". A rule a line rests on
 * waits behind its book's name. The server sends only what the books hold, so a
 * narrator they do not mention gets no empty group, and none while usul.db is not built.
 */
import HADITH from '../../hadith.json'

import ArabicText from './ArabicText'
import Disclosure from './Disclosure'
import ShowRest from './ShowRest'
import SourceBadge from './SourceBadge'

const GROUPS = [
  ['reliability', 'Reliability'],
  ['habits', 'Habits in hadith'],
  ['life', 'Life'],
  ['books', 'In our books'],
]

const { quoteLetters: WHOLE_UP_TO, quoteLines: LINES } = HADITH.narrator

/** The book's words, whole while short, else cut to a snippet. */
function Quote({ children, accent }) {
  const words = <ArabicText as="p" size="sm" className="block m-0 text-[var(--text-faint)]">{children}</ArabicText>
  return children.length <= WHOLE_UP_TO ? words : <ShowRest lines={LINES} accent={accent} more="Show the rest">{words}</ShowRest>
}

function Line({ line, source, accent }) {
  return (
    <li className="space-y-1.5">
      <p className="type-ui m-0 text-[var(--text)]">{line.text}</p>
      {line.ar && <ArabicText as="p" size="base" className="block m-0 leading-relaxed">{line.ar}</ArabicText>}
      {line.quote && <Quote accent={accent}>{line.quote}</Quote>}
      {line.rule && (
        <Disclosure label={`Rule: ${[line.rule.book, line.rule.page].filter(Boolean).join(', ')}`}>
          <p className="type-small m-0 mb-1 text-[var(--text-dim)]">{line.rule.say}</p>
          <ArabicText as="p" size="sm" className="block m-0 leading-loose text-[var(--text-faint)]">{line.rule.quote}</ArabicText>
        </Disclosure>
      )}
      <SourceBadge source={source && { ...source, label: [line.book, line.page].filter(Boolean).join(', ') }} />
    </li>
  )
}

export default function BookFacts({ usul, accent }) {
  const shown = GROUPS.filter(([key]) => usul?.[key]?.length)
  if (!shown.length) return null
  return (
    <section aria-label="What the narrator books say" className="grid gap-x-6 gap-y-5 grid-cols-[repeat(auto-fit,minmax(min(100%,18rem),1fr))] [&>*]:min-w-0">
      {shown.map(([key, title]) => (
        <div key={key} className="space-y-2">
          <h3 className="type-ui font-medium text-[var(--text)]">{title}</h3>
          <ul className="list-none m-0 p-0 space-y-4">
            {usul[key].map((line, i) => <Line key={`${line.text}${line.ar}${i}`} line={line} source={usul.source} accent={accent} />)}
          </ul>
        </div>
      ))}
    </section>
  )
}
