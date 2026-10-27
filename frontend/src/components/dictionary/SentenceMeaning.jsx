/**
 * A phrase or sentence asked of the dictionary: its sense, then word by word,
 * the way al-Maany sets the two out. The sense sits in the card with the
 * Arabic, as the ayah view's translation does; the words sit under it, each one
 * a way into its own dictionary entry.
 */
import ArabicText from '../ui/text/ArabicText'
import { GoButton } from '../ui/buttons/RootActions'
import SourceBadge from '../ui/feedback/SourceBadge'
import TranslationStrip from '../ui/text/TranslationStrip'

// `bare` drops what the analyser already says around it: the kind line, who translated it,
// and the word-by-word list, which its chart shows on hover.
export default function SentenceMeaning({ data, accent, onGo, onLookup, bare = false }) {
  // English typed: the sentence is English and the Arabic rendering is the answer.
  const toArabic = data.direction === 'en'
  return (
    <div className="space-y-4">
      {!(bare && !data.ref) && <div className="flex items-center justify-between gap-3 flex-wrap">
        {!bare && <p className="text-[var(--text-dim)] type-body capitalize">{data.kind}</p>}
        {data.ref && onGo && (
          <GoButton onClick={() => onGo('quran', data.ref)} style={{ '--c': accent }}>
            Open ayah {data.ref}
          </GoButton>
        )}
      </div>}

      <div className="rise-in rounded-[var(--radius-lg)] bg-[var(--surface)] border border-[var(--border)] overflow-hidden">
        {toArabic
          ? <p className="p-5 type-body text-[var(--text)]" lang="en">{data.query}</p>
          : <ArabicText as="p" size="lg" className="p-5 text-[var(--text)]">{data.query}</ArabicText>}
        <TranslationStrip source={bare ? null : data.source}>
          {data.meaning
            ? (toArabic
              ? <ArabicText as="p" size="lg" className="text-[var(--text)]">{data.meaning}</ArabicText>
              : <p className="type-body text-[var(--text)] leading-relaxed">{data.meaning}</p>)
            : <p className="type-body text-[var(--text-dim)]">The translator could not be reached, so only the words below.</p>}
        </TranslationStrip>
      </div>
      {data.left_out?.length > 0 && (
        <p className="type-small text-[var(--text-dim)]">Left out, not Arabic: {data.left_out.join(', ')}</p>
      )}

      {!bare && <>
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h3 className="text-sm text-[var(--text-dim)]">Word by word</h3>
        <SourceBadge source={data.words_source} />
      </div>
      <div className="flex flex-wrap justify-center gap-2" dir={toArabic ? 'ltr' : 'rtl'}>
        {data.words.map((w, i) => (
          <button
            key={i}
            type="button"
            disabled={toArabic && !w.arabic}
            onClick={() => onLookup(toArabic ? w.arabic : w.base)}
            title={toArabic ? `Look up ${w.english}` : `Look up ${w.base}`}
            style={{ '--i': i }}
            className="word rise-in flex flex-col items-center gap-1 p-2.5 rounded-[var(--radius-md)]
              bg-[var(--surface)] border border-[var(--border)] transition-colors hover:border-[var(--text-faint)]"
          >
            {toArabic
              ? <span className="type-small text-[var(--text-dim)]" lang="en">{w.english} →</span>
              : <ArabicText className="text-[var(--text)] leading-tight">{w.arabic}</ArabicText>}
            {toArabic
              ? <ArabicText className="text-[var(--text)] leading-tight">{w.arabic || '—'}</ArabicText>
              : <span className="type-small text-[var(--text-dim)] max-w-[7rem] text-center" lang="en" dir="ltr">
                {w.english}
              </span>}
          </button>
        ))}
      </div>
      </>}
    </div>
  )
}
