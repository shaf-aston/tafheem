/**
 * The Nahw notes: reading the marks in a note, and turning the same marks into
 * a test or a pack of cards.
 *
 * A note is stored once, whole, with the testable pieces marked in place:
 * `الحال {{ruling|منصوب}} أبدا`. Nothing here rewrites a note. Hiding is a
 * decision made when the page is opened, so the stored note stays the
 * reference and changing what is tested is a setting, not a rebuild.
 *
 * Pure functions throughout: a topic and a choice of roles in, parts and cards
 * out. No React, no fetching, no randomness.
 */
import settings from '../notes.json'

/** Every setting the notes panel reads, the way tamreen.js maps tamreen.json. */
export const NOTES = {
  hide: settings.hide,
  cardsPerRun: settings['cards-per-run'],
  revealStays: settings['reveal-stays'],
}

const MARK = /\{\{([^{}|]+)\|([^{}]*)\}\}/g

/** One string split into the plain runs and the marked pieces, in order. */
export function parseMarked(text) {
  const parts = []
  let at = 0
  for (const found of (text ?? '').matchAll(MARK)) {
    if (found.index > at) parts.push({ text: text.slice(at, found.index), role: null })
    parts.push({ text: found[2], role: found[1] })
    at = found.index + found[0].length
  }
  if (at < (text ?? '').length) parts.push({ text: text.slice(at), role: null })
  return parts
}

/** The teacher's own wording back, with every mark taken off. */
export function stripMarks(text) {
  return (text ?? '').replace(MARK, '$2')
}

/**
 * Every string a reader sees in a block, with where it lives: fields, list
 * lines and table cells. The API sends a field a block does not have as null.
 */
function linesOf(block) {
  const lines = []
  for (const [field, value] of Object.entries(block)) {
    if (field === 'id' || field === 'kind' || value == null) continue
    if (typeof value === 'string') lines.push([field, value])
    else if (field === 'items') value.forEach((line, i) => lines.push([`items.${i}`, line]))
    else if (field === 'rows') value.forEach((row, r) => row.forEach((cell, c) => lines.push([`rows.${r}.${c}`, cell])))
  }
  return lines
}

/**
 * Every marked piece in a block, with the line it sits in and where in that
 * line it is. The place matters: the same words can appear plainly earlier in
 * the line, and blanking the first match would gap the wrong one.
 */
export function markedIn(block) {
  const found = []
  for (const [field, text] of linesOf(block)) {
    const parts = parseMarked(text)
    parts.forEach((part, at) => {
      if (part.role) found.push({ field, role: part.role, text: part.text, parts, at })
    })
  }
  return found
}

/** The line a piece sits in, with that one piece blanked out and every other mark taken off. */
export function gapped(piece, blank = '_____') {
  return piece.parts.map((part, i) => (i === piece.at ? blank : part.text)).join('')
}

/** Which roles a whole topic actually marks, so the page only offers switches that do something. */
export function rolesUsed(topic) {
  const used = new Set()
  for (const block of topic?.blocks ?? []) {
    for (const piece of markedIn(block)) used.add(piece.role)
  }
  return used
}

const asked = (block) => (block.answer_col ?? null) !== null

/**
 * The cards a topic gives, in page order.
 *
 * Three kinds, and all three come from what is already in the note: a marked
 * piece of a chosen role (the line with a gap in it, the piece behind), a table
 * row (the rest of the row, the answered column behind), and, when labels are
 * chosen, an example's labelled word (the sentence and the word, what it is
 * called behind). Table rows come whatever the roles: a table that names an
 * `answer_col` has said itself what it asks. Two identical rows in a
 * table are two cards, not one: the note has them twice and a reader drilling
 * them will meet them twice.
 */
export function cardsOf(topic, roles = NOTES.hide) {
  const wanted = new Set(roles)
  const cards = []
  for (const block of topic?.blocks ?? []) {
    for (const piece of markedIn(block)) {
      if (!wanted.has(piece.role)) continue
      // A cell in the column a table already asks for is carried by the row card.
      if (asked(block) && piece.field.startsWith('rows.') && piece.field.endsWith(`.${block.answer_col}`)) continue
      cards.push({
        kind: 'piece',
        blockId: block.id,
        page: block.page,
        role: piece.role,
        front: gapped(piece),
        back: piece.text,
      })
    }
    if (block.kind === 'table' && asked(block)) {
      for (const row of block.rows ?? []) {
        const shown = row.filter((_, i) => i !== block.answer_col).map(stripMarks)
        cards.push({
          kind: 'row',
          blockId: block.id,
          page: block.page,
          role: null,
          front: [stripMarks(block.caption ?? ''), ...shown].filter(Boolean).join(' · '),
          back: stripMarks(row[block.answer_col]),
        })
      }
    }
    if (!wanted.has('label')) continue
    for (const label of block.labels ?? []) {
      cards.push({
        kind: 'label',
        blockId: block.id,
        page: block.page,
        role: 'label',
        front: `${stripMarks(block.ar ?? '')} · ${label.word}`,
        back: label.label,
      })
    }
  }
  return cards
}

/** One run's worth of cards, taken in order from a starting point so nothing is lost. */
export function runOf(cards, from = 0, size = NOTES.cardsPerRun) {
  return cards.slice(from, from + size)
}
