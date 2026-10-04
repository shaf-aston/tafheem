/**
 * A word's colour comes from the key the backend sends and from nothing else.
 * Role keys are copied from schemas.ROLE_KEYS.
 */
import { describe, expect, it } from 'vitest'

import { GLOSSARY, caseLabel, typeLabel } from './grammarTerms'
import { roleVar } from './roleColors'

// The role names the backend can send, schemas.ROLE_KEYS.
const KEYS = ['fil', 'fail', 'mubtada', 'khabar', 'mafool', 'sifah', 'haal', 'mudaf', 'harf', 'mansub', 'tabi']

describe('roleVar', () => {
  it('turns a role name into that role\'s own token', () => {
    for (const key of KEYS) expect(roleVar(key)).toBe(`var(--role-${key})`)
  })

  // The bug this file exists for: a word whose role was written in Arabic prose
  // must be coloured by its key, never by what the prose happens to contain.
  it('never reads the Arabic role text', () => {
    expect(roleVar('fail')).toBe('var(--role-fail)')
    expect(roleVar('fail')).not.toBe(roleVar(null))
  })

  // "Not settled" has to look different from every settled role, or the grid
  // would claim to know something it does not.
  it('falls back to the neutral colour when there is no role', () => {
    for (const nothing of [null, undefined, '']) {
      expect(roleVar(nothing)).toBe('var(--role-default)')
    }
  })
})

describe('the glossary', () => {
  // A tag prints the Arabic term alone; the English lives in the glossary.
  it('names a case in Arabic, and leaves an unknown case as it came', () => {
    expect(caseLabel('nasb')).toBe('منصوب')
    expect(caseLabel("raf'")).toBe('مرفوع')
    expect(caseLabel('jarr')).toBe('مجرور')
    expect(caseLabel('mabni')).toBe('مبني')
    expect(caseLabel('jazm')).toBe('مجزوم')
    expect(caseLabel('mabni (سكون على اللام)')).toBe('مبني (سكون على اللام)')
    expect(caseLabel('odd')).toBe('odd')
  })

  it('names a word type in Arabic, and leaves an unknown one as it came', () => {
    expect(typeLabel('ism')).toBe('اسم')
    expect(typeLabel("fi'l")).toBe('فعل')
    expect(typeLabel('punc')).toBe('punc')
  })

  // Completeness against what the backend prints: tests/test_rule_engine.py.
  it('lists every term once, each with Arabic and a meaning', () => {
    const terms = GLOSSARY.flatMap((section) => section.terms)
    expect(new Set(terms.map((t) => t.arabic)).size).toBe(terms.length)
    for (const t of terms) {
      expect(t.arabic).toMatch(/[؀-ۿ]/)
      expect(t.meaning, t.arabic).toBeTruthy()
    }
  })
})
