/**
 * One line of a page: the Arabic, then its English under it.
 *
 * The line is always the page's own text, its commas and full stops kept, so
 * what is copied from here (into Nahw, say) is what the page said. Once the
 * translation arrives each word the translator also read becomes a PageWord
 * (matched in order, vowel marks aside); a word it skipped stays plain text.
 * A line from inside the Qur'an says which ayah, the way the sentence view does.
 */
import { GoButton } from '../ui/buttons/RootActions'
import ArabicText from '../ui/text/ArabicText'
import { smartError } from '../../lib/api/apiError'
import { isArabic } from '../../lib/text/arabicText'
import { matched } from '../../lib/dictionary/pageLines'
import PageWord from './PageWord'

export default function PageLine({ line, found, accent, onLookup, onGo }) {
  const data = found?.data
  const words = data?.words?.length ? data.words : []
  return (
    <li
      style={{ '--c': accent }}
      className={`rise-in flex flex-col gap-2 p-4 rounded-[var(--radius-lg)] bg-[var(--surface)] border border-[var(--border)]
        ${line.opensParagraph ? 'mt-3' : ''}`}
    >
      <ArabicText as="p" size="lg" className="text-[var(--text)] leading-loose">
        {matched(line.text, words).map(({ before, core, word, after }, i) => (
          <span key={i}>
            {i > 0 && ' '}{before}{word ? <PageWord word={word} onLookup={onLookup} /> : core}{after}
          </span>
        ))}
      </ArabicText>
      <English line={line} found={found} />
      {data?.ref && onGo && (
        <div>
          <GoButton onClick={() => onGo('quran', data.ref)} style={{ '--c': accent }}>Ayah {data.ref}</GoButton>
        </div>
      )}
    </li>
  )
}

function English({ line, found }) {
  const dim = 'type-small text-[var(--text-faint)]'
  if (!isArabic(line.text)) return <p className={dim}>Not Arabic, so not translated.</p>
  if (!found || found.state === 'asking') return <p className={`${dim} animate-pulse`}>Translating…</p>
  if (found.state === 'paused') return <p className={dim}>Many lines at once; waiting a moment for the translator…</p>
  if (found.state === 'failed') return <p className={dim}>{smartError(found.error, 'This line could not be translated.')}</p>
  if (!found.data.meaning) return <p className={dim}>The translator could not be reached; hover a word for its meaning.</p>
  return <p className="type-body text-[var(--text-dim)] leading-relaxed" lang="en">{found.data.meaning}</p>
}
