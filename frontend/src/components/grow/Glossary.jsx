/**
 * A book's glossary on its page: each term, its Arabic, what it means (the book file's `glossary`), and a button to the
 * lesson that teaches it. Folded away; a filter narrows it.
 */
import { useState } from 'react'

import { lessonsOf } from '../../lib/bookLesson'
import { sayIn } from '../../lib/say'
import ArabicText from '../ui/ArabicText'

const say = sayIn('en')

/** The book's terms, folded away; a filter narrows them, and each opens the lesson that teaches it. */
export default function Glossary({ book, onStart }) {
  const [find, setFind] = useState('')
  const terms = book.glossary ?? []
  if (!terms.length) return null
  const lessons = new Map(lessonsOf(book).map((lesson) => [lesson.id, lesson]))
  const looking = find.trim().toLowerCase()
  const shown = terms.filter((one) => !looking || `${one.term} ${one.ar} ${one.en}`.toLowerCase().includes(looking))
  return (
    <details className="grow-glossary">
      <summary>{say('Glossary · {n} terms', { n: terms.length })}</summary>
      <input type="search" value={find} onChange={(event) => setFind(event.target.value)} placeholder={say('Find a term')}
        aria-label={say('Find a term')} />
      <dl>
        {shown.map((one) => {
          const lesson = lessons.get(one.lesson)
          return (
            <div key={one.term}>
              <dt><b>{one.term}</b> <ArabicText size="sm">{one.ar}</ArabicText></dt>
              <dd>
                {one.en}
                {lesson && (
                  <button type="button" onClick={() => onStart(lesson.id, lesson.part)}>{say('Lesson: {title}', { title: lesson.title })}</button>
                )}
              </dd>
            </div>
          )
        })}
      </dl>
      {!shown.length && <p className="grow-hint">{say('No term matches.')}</p>}
    </details>
  )
}
