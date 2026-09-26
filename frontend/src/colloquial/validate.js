/**
 * Checks unit files against unit.schema.json (shape) and colloquial.json
 * (rules). Reports only: content is the author's to fix, so nothing here edits,
 * renames or fills in anything. Pure, no file access, so the CLI and the tests
 * share it.
 */
import config from '../colloquial.json'
import { spokenForm } from '../lib/arabicText'
import schema from './unit.schema.json'

const TYPES = config['exercise-types']
const MINIMUMS = config['lesson-minimums']
// Lists a type may carry, straight from the config, so a new list is one line there.
const TYPE_LISTS = Object.keys(Object.values(TYPES)[0])

const typeOf = (v) => (v === null ? 'null' : Array.isArray(v) ? 'array' : typeof v)

/** Walks the handful of keywords unit.schema.json uses; returns [{path, problem}]. */
export function checkSchema(value, node = schema, path = '') {
  const allowed = [node.type].flat()
  if (!allowed.includes(typeOf(value))) return [{ path, problem: `expected ${allowed.join(' or ')}, got ${typeOf(value)}` }]
  const out = []
  if (node.enum && !node.enum.includes(value)) out.push({ path, problem: `"${value}" is not one of ${node.enum.join(', ')}` })
  if (node.pattern && !new RegExp(node.pattern).test(value)) out.push({ path, problem: `"${value}" does not match ${node.pattern}` })
  if (typeOf(value) === 'array') {
    if (value.length < (node.minItems ?? 0)) out.push({ path, problem: `needs at least ${node.minItems}` })
    value.forEach((v, i) => out.push(...checkSchema(v, node.items, `${path}[${i}]`)))
  }
  if (typeOf(value) === 'object' && node.properties) {
    const at = (k) => (path ? `${path}.${k}` : k)
    for (const k of node.required ?? []) if (!(k in value)) out.push({ path: at(k), problem: 'missing' })
    for (const [k, v] of Object.entries(value)) {
      if (node.properties[k]) out.push(...checkSchema(v, node.properties[k], at(k)))
      else if (node.additionalProperties === false) out.push({ path: at(k), problem: 'unexpected key' })
    }
  }
  return out
}

const blank = (s) => typeof s !== 'string' || !s.trim()

/** Rules beyond shape for one lesson; returns problem strings. */
export function checkLesson(lesson) {
  const out = []
  for (const [list, min] of Object.entries(MINIMUMS)) {
    const n = lesson[list]?.length ?? 0
    if (n < min) out.push(`${list}: ${n}, needs at least ${min}`)
  }
  const seen = new Set()
  for (const ex of lesson.exercises ?? []) {
    const at = `exercise ${ex.id}`
    if (seen.has(ex.id)) out.push(`${at}: duplicate exercise id`)
    seen.add(ex.id)
    const rule = TYPES[ex.type]
    if (rule) {
      for (const list of TYPE_LISTS) {
        const has = (ex[list]?.length ?? 0) > 0
        if (rule[list] && !has) out.push(`${at}: ${ex.type} needs ${list}`)
        if (!rule[list] && has) out.push(`${at}: ${list} is only for ${Object.keys(TYPES).filter((t) => TYPES[t][list]).join(', ')}`)
      }
    }
    if (blank(ex.answer)) out.push(`${at}: answer is empty`)
    if (blank(ex.tip)) out.push(`${at}: tip is empty`)
    if (!ex.accepted?.some((a) => !blank(a))) out.push(`${at}: accepted needs at least one form`)
    const natural = new Set([ex.answer, ...(ex.accepted ?? [])].map(spokenForm))
    for (const f of ex.too_formal ?? []) {
      if (natural.has(spokenForm(f.answer))) out.push(`${at}: "${f.answer}" is both accepted and too_formal`)
    }
  }
  return out
}

/**
 * Every unit, keyed by file name. Returns [{file, lesson, problem}]; lesson is
 * null for problems outside a lesson.
 */
export function validateAll(units) {
  const out = []
  const owner = new Map()
  for (const [file, unit] of Object.entries(units)) {
    for (const { path, problem } of checkSchema(unit)) {
      const i = path.match(/^lessons\[(\d+)\]/)?.[1]
      out.push({ file, lesson: i === undefined ? null : unit.lessons[i]?.id ?? `#${i}`, problem: `${path}: ${problem}` })
    }
    for (const lesson of Array.isArray(unit?.lessons) ? unit.lessons : []) {
      if (typeOf(lesson) !== 'object') continue
      for (const problem of checkLesson(lesson)) out.push({ file, lesson: lesson.id, problem })
      if (owner.has(lesson.id)) out.push({ file, lesson: lesson.id, problem: `lesson id also used in ${owner.get(lesson.id)}` })
      else owner.set(lesson.id, file)
    }
  }
  return out
}

/** file → lesson → problem, as readable lines. */
export function formatReport(problems, fileCount) {
  const lines = [`${fileCount} unit file(s), ${problems.length} problem(s)`]
  let file, lesson
  for (const p of problems) {
    if (p.file !== file) (lines.push(`\n${p.file}`), (file = p.file), (lesson = undefined))
    if (p.lesson !== lesson) (lines.push(`  ${p.lesson ?? '(unit)'}`), (lesson = p.lesson))
    lines.push(`    - ${p.problem}`)
  }
  return lines.join('\n')
}
