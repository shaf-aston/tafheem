/**
 * A Tamreen example's sentence, marked the way the picture marks it: blue
 * underline for a possible حال, green for a possible ذو الحال. One definition
 * so Practise and Browse draw the same sentence the same way.
 */
import { markedWords, sentenceLines } from '../lib/tamreen'
import ArabicText from './ui/ArabicText'

export function TamreenLegend() {
  return (
    <div className="flex gap-4 type-small text-[var(--text-faint)] flex-wrap">
      <span className="flex items-center gap-1.5">
        <span aria-hidden="true" className="inline-block w-3.5 h-0.5" style={{ background: 'var(--tamreen-haal)' }} />
        possible حال
      </span>
      <span className="flex items-center gap-1.5">
        <span aria-hidden="true" className="inline-block w-3.5 h-0.5" style={{ background: 'var(--tamreen-zulhaal)' }} />
        possible ذو الحال
      </span>
    </div>
  )
}

export default function TamreenSentence({ example, size = 'lg' }) {
  const { arabic, gloss } = sentenceLines(example)
  const { blue, green } = markedWords(example)
  const words = arabic.split(/\s+/).filter(Boolean)

  return (
    <div className="space-y-1">
      <ArabicText size={size} className="block leading-loose text-right" dir="rtl">
        {words.map((word, i) => {
          const color = blue.has(word) ? 'var(--tamreen-haal)' : green.has(word) ? 'var(--tamreen-zulhaal)' : undefined
          return (
            <span
              key={i}
              style={color ? { textDecoration: `underline 3px ${color}`, textUnderlineOffset: '8px' } : undefined}
            >
              {word}
              {i < words.length - 1 ? ' ' : ''}
            </span>
          )
        })}
      </ArabicText>
      {gloss && <p className="type-small text-[var(--text-dim)]">{gloss}</p>}
    </div>
  )
}
