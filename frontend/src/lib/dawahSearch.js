// Search over the dawah questions: every word typed must appear somewhere in
// the question, its reply, its point headings, its address or its topic.
// Latin and Arabic letters count; vowel marks do not, so الصبر finds الصَّبْر.
import { foldForSearch } from './arabicText'

const fold = (text) => foldForSearch(text).replace(/[^a-z0-9؀-ۿ ]/g, ' ')

export const matches = (query, topic, question) => {
  const titles = question.points.map((point) => point.title).join(' ')
  const hay = fold(`${question.q} ${question.short} ${titles} ${question.id.replace(/-/g, ' ')} ${topic.title}`)
  return fold(query).split(/\s+/).filter(Boolean).every((word) => hay.includes(word))
}
