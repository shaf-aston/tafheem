import { GoButton } from '../../ui/buttons/RootActions'
import SentenceMeaning from '../../ui/text/SentenceMeaning'
import TranslationStrip from '../../ui/text/TranslationStrip'

// The foot of the tree's card: the English, beside the chart's tools. The tree
// already writes the sentence out, so the English is not set under a third copy
// of it. The tools are there before the English arrives, so nothing moves.
export function EnglishFoot({ meaning, accent, onGo, children }) {
  const data = meaning.data?.words ? meaning.data : null
  return (
    <TranslationStrip pad="px-5 py-3" className="rounded-b-[var(--radius-lg)] flex flex-wrap items-center gap-x-3 gap-y-2">
      {/* Too little room beside the tools (a phone, Merged/Split shown): they drop under it. */}
      <div className="flex-[1_1_10rem] min-w-0 space-y-2 rise-in">
        {data && (
          <p lang="en" className={`type-body leading-relaxed ${data.meaning ? 'text-[var(--text)]' : 'text-[var(--text-dim)]'}`}>
            {data.meaning || 'The translator could not be reached, so only the words below.'}
          </p>
        )}
        {data?.left_out?.length > 0 && (
          <p className="type-small text-[var(--text-dim)]">Left out, not Arabic: {data.left_out.join(', ')}</p>
        )}
        {data?.ref && onGo && (
          <GoButton onClick={() => onGo('quran', data.ref)} style={{ '--c': accent }}>Open ayah {data.ref}</GoButton>
        )}
      </div>
      <div className="ml-auto flex items-center gap-2">{children}</div>
    </TranslationStrip>
  )
}

// With no tree, the sentence's own card: the Arabic, then the English under it.
// The card above already says what it is, so no heading names it again.
export function EnglishMeaning({ meaning, accent, onGo }) {
  if (!meaning.data?.words) return null
  return (
    <section aria-label="English meaning" className="rise-in">
      <SentenceMeaning data={meaning.data} accent={accent} onGo={onGo} bare
        onLookup={(w) => onGo?.('dict', w)} />
    </section>
  )
}
