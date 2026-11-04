/**
 * The verb patterns (forms II–X) for the Basics world: what each adds to a verb's meaning. Pure.
 *
 * A family is one root's verbs on several patterns (public/grow/basics-verbs.json `families`, whose Arabic the
 * conjugation engine made), each with its hand-checked English: عَلِمَ he knew · عَلَّمَ he taught · تَعَلَّمَ he learnt.
 * Each pattern is asked two ways: what the pattern adds (shown one of its verbs), and what one verb on it means, set
 * beside its form I. What a pattern adds is a tendency, not a rule, so a verb's own meaning is always the one asked.
 * Form VI is said of "they" (they did it to each other), so its verbs are the past for "they".
 */
import { MODULE } from './alifLam'
import { englishOptions } from './wordForms'
import { shuffled } from '../text/shuffle'

/** Each pattern: its shape on فعل, what it adds, and the patterns whose meaning is too close to set beside it. */
export const PATTERNS = {
  II: { shape: 'فَعَّلَ', adds: 'making someone do it, or doing it a lot', near: ['IV'] },
  III: { shape: 'فَاعَلَ', adds: 'doing it with or to someone', near: [] },
  IV: { shape: 'أَفْعَلَ', adds: 'making someone do it', near: ['II'] },
  V: { shape: 'تَفَعَّلَ', adds: 'doing it to yourself', near: ['VII', 'VIII'] },
  VI: { shape: 'تَفَاعَلَ', adds: 'doing it to each other', near: [] },
  VII: { shape: 'اِنْفَعَلَ', adds: 'it getting done, by itself', near: ['V', 'VIII'] },
  VIII: { shape: 'اِفْتَعَلَ', adds: 'doing it for yourself, with effort', near: ['V', 'VII'] },
  X: { shape: 'اِسْتَفْعَلَ', adds: 'asking for it', near: [] },
}

/** A family's verbs as table entries: `I`, `II`… each { key, ar, en }. */
export const familyTable = (family) => Object.entries(family.forms).map(([key, { ar, en }]) => ({ key, ar, en }))

const pick = (list, random) => list[Math.floor(random() * list.length)]
const tagOf = (isNew) => (isNew ? 'New form' : 'Review')
const record = (item, direction, asked, family) => ({
  module: MODULE, item: item.id, context: { world: MODULE, skill: item.skill, direction, word: asked.ar, from: family.id },
})

/** "What does اِسْتَفْعَلَ add?" on one of its verbs: what it adds, and two patterns that add something else. */
function addsCard(item, isNew, random, family) {
  const form = item.marker.key
  const table = familyTable(family)
  const [base, asked] = ['I', form].map((key) => table.find((entry) => entry.key === key))
  const pattern = PATTERNS[form]
  const others = Object.keys(PATTERNS).filter((one) => one !== form && !pattern.near.includes(one))
  const wrong = shuffled(others, random).slice(0, 2)
  const said = `${asked.ar} = ${asked.en}, and ${base.ar} = ${base.en}.`
  return {
    kind: 'choose',
    id: `adds:${item.id}`,
    tag: tagOf(isNew),
    ask: `It is on the pattern ${pattern.shape}. What does that pattern add?`,
    ar: asked.ar,
    options: shuffled([{ id: 'right', text: pattern.adds }, ...wrong.map((one) => ({ id: one, text: PATTERNS[one].adds }))], random),
    answer: 'right',
    why: `${said} ${pattern.shape} often adds ${pattern.adds}.`,
    wrong: Object.fromEntries(wrong.map((one) => [one, `${said} ${pattern.shape} often adds ${pattern.adds}; ${PATTERNS[one].shape} adds ${PATTERNS[one].adds}.`])),
    record: record(item, 'adds', asked, family),
  }
}

/** "عَلِمَ is ‘he knew’. What does تَعَلَّمَ mean?": the verb's meaning and two of its family's others. */
function readCard(item, isNew, random, family) {
  const form = item.marker.key
  const table = familyTable(family)
  const [base, asked] = ['I', form].map((key) => table.find((entry) => entry.key === key))
  const pool = table.filter((entry) => entry.key !== form).map((entry) => entry.key)
  const options = englishOptions(table, form, pool, random)
  const said = `${asked.ar} = ${asked.en}.`
  const adds = `${PATTERNS[form].shape} often adds ${PATTERNS[form].adds}.`
  return {
    kind: 'choose',
    id: `read:${item.id}`,
    tag: tagOf(isNew),
    ask: `${base.ar} is “${base.en}”. What does this one mean?`,
    ar: asked.ar,
    options,
    answer: 'right',
    why: `${said} ${adds}`,
    wrong: Object.fromEntries(options.filter((one) => one.id !== 'right').map(({ id }) => {
      const one = table.find((entry) => entry.key === id)
      return [id, `${said} ${one.ar} is “${one.en}”. ${adds}`]
    })),
    record: record(item, 'to-english', asked, family),
  }
}

/** A pattern's two questions, each on a family of its own. */
export const patternAsks = (item, isNew, random) => [
  addsCard(item, isNew, random, pick(item.words, random)),
  readCard(item, isNew, random, pick(item.words, random)),
]
