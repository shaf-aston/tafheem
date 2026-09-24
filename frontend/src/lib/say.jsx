/**
 * The interface in the reader's own language.
 *
 * The English sentence is the key. One file to write instead of two; a sentence
 * nobody has translated yet falls back to the English already written in the
 * code, which is the honest thing to show and never a bare key; and the JSX
 * still reads as the sentence it renders.
 *
 * `{name}` in a sentence is a slot. say() fills it with text, fill() fills it
 * with an element, which is what the correction line needs: "{word} means
 * {meaning}" puts its verb in the middle in English and wraps the pair in
 * "کا مطلب … ہے" in Urdu, so the whole sentence has to be one key and the
 * language decides where the two words land, not the code.
 *
 * Only the quiz is translated so far. Everything else is English, and the words
 * being taught, surah names, topic names, are content rather than interface and
 * stay as the source wrote them.
 */
import { Fragment } from 'react'

import ur from '../lang/ur.json'

const TABLES = { ur }
const SLOT = /(\{\w+\})/
const SLOT_NAME = /^\{(\w+)\}$/

/** The sentences for one language. English is the source, so it has no table. */
const tableFor = (language) => TABLES[language] ?? {}

/** say('Next word') and say('Only {n} words here.', { n: 3 }). */
export function sayIn(language) {
  const table = tableFor(language)
  return (english, values) => {
    const text = table[english] ?? english
    if (!values) return text
    return text.replace(/\{(\w+)\}/g, (slot, name) => (name in values ? String(values[name]) : slot))
  }
}

/**
 * The same, where the slots are elements: returns the pieces in the order this
 * language puts them, ready to render.
 */
export function fillIn(language) {
  const table = tableFor(language)
  return (english, nodes) => (table[english] ?? english)
    .split(SLOT)
    .map((piece, at) => {
      const name = SLOT_NAME.exec(piece)?.[1]
      return name ? <Fragment key={at}>{nodes[name]}</Fragment> : piece
    })
}
