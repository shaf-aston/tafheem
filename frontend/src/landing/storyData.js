import { loadDemo } from './loadDemo.js'

// Every word of the demo sentence with the role and colour the real analysis
// gave it, in reading order.
function leaves(node, out = []) {
  if (node.children?.length) node.children.forEach((c) => leaves(c, out))
  else if (node.word != null) out[node.word] = { role: node.role, tone: node.tone }
  return out
}
const demo = loadDemo()
export const DEMO_WORDS = leaves(demo.tree).map((l, i) => ({ word: demo.words[i], ...l }))

// The two governor arrows of step 2: the particle إنّ (word 0) reaches the
// noun it puts in the accusative (word 1) and the verb reaches its object (word 4).
export const GOVERNS = [
  { from: 0, to: 1, why: ['الطَّالِبَ', 'is mansub. ', 'إنَّ', ' governs it and puts it in the accusative.'] },
  { from: 3, to: 4, why: ['الرِّسَالَةَ', 'is the object of ', 'كَتَبَ', ', so it is accusative too.'] },
]

// Step 4: the words the root ك ت ب gives, each with the angle (degrees) it
// settles at around the letters on a wide screen.
export const ROOT_WORDS = [
  ['كَتَبَ', 'he wrote', 215],
  ['كِتَاب', 'book', 325],
  ['كَاتِب', 'writer', 180],
  ['مَكْتَب', 'desk, office', 0],
  ['مَكْتُوب', 'written', 145],
  ['مَكْتَبَة', 'library', 35],
]
export const ROOT_LETTERS = ['ك', 'ت', 'ب']

export const BOOKS = [
  ['Maqayis', 'origin sense'],
  ['Lisan al-Arab', 'full entry'],
  ['Taj al-Arus', 'commentary'],
  ['Lane', 'English'],
]
