/**
 * One word's full grammar and root, shown inline in the page flow. Used by
 * both Nahw's word grid and AyahStudy's reading line, so the two tabs cannot
 * drift into showing different facts for the same kind of word.
 *
 * Not a dialog: an overlay put half the card off screen for a word at the
 * line's right edge, and covered the words on the line below so the next one
 * could not be tapped. Escape still closes it, and opening moves focus and
 * scroll to the card, but there is no backdrop and no focus trap.
 */
import { useEffect, useRef } from 'react'

import { caseLabel, posLabel, signLabel, typeLabel } from '../lib/grammarTerms'
import { roleVar } from '../lib/roleColors'
import { scrollToEl } from '../lib/scrollToEl'
import ArabicText from './ui/ArabicText'
import RootActions from './ui/RootActions'

export default function WordCard({ word, onClose, onGo, exclude }) {
  const headingRef = useRef(null)
  const key = word?.role_key
  const hasPieces = word?.segments?.length > 1

  useEffect(() => {
    if (!word) return
    headingRef.current?.focus()
    scrollToEl(headingRef.current, 'nearest')
  }, [word])

  useEffect(() => {
    if (!word) return
    const onKeyDown = (e) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [word, onClose])

  if (!word) return null

  return (
    <div
      style={{ '--c': roleVar(key) }}
      className="fade-in role glow rounded-[var(--radius-lg)] p-4
        bg-[var(--surface)] border space-y-2.5"
    >
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div ref={headingRef} tabIndex={-1} className="flex items-baseline gap-2.5 flex-wrap outline-none">
          <ArabicText as="span" size="lg" className="text-glow">
            {word.word || word.arabic}
          </ArabicText>
          {word.pos && (
            <ArabicText size="tiny" style={{ color: 'var(--c)' }}>{posLabel(word.pos)}</ArabicText>
          )}
          {word.meaning && (
            <span className="type-small text-[var(--text-dim)]">{word.meaning}</span>
          )}
        </div>
        <button
          type="button"
          onClick={onClose}
          className="type-small text-[var(--text-faint)] hover:text-[var(--text)]
            underline underline-offset-2 transition-colors"
        >
          Close
        </button>
      </div>

      {word.role && (
        <div className="flex flex-col items-center gap-2">
          <span
            style={{ '--c': roleVar(key) }}
            className="px-3 py-1 rounded-full type-small font-medium role-tag"
          >
            {word.role}
          </span>
        </div>
      )}

      {/* Only when the source speaks in sentences (segments/lemma) rather than
          case/sign pairs; a corpus word with no grammar array still says so. */}
      {(word.grammar || word.segments || word.lemma) && (
        word.grammar?.length
          ? <ArabicText as="p" size="sm" className="text-[var(--text)] leading-relaxed">{word.grammar.join(' · ')}</ArabicText>
          : <p className="type-small text-[var(--text)]">No grammar recorded for this word.</p>
      )}

      {word.lemma && (
        <p className="type-small text-[var(--text-faint)]">
          Dictionary form{' '}
          <ArabicText className="text-[var(--text-dim)]">{word.lemma}</ArabicText>
        </p>
      )}

      {/* How the word is built up, when it is more than one piece: the
          prefix, the word, the ending, each with its own job. */}
      {hasPieces && (
        <ul className="space-y-0.5">
          {word.segments.map((piece, i) => (
            <li key={i} className="type-small text-[var(--text-faint)] flex gap-1.5">
              <ArabicText className="text-[var(--text-dim)] shrink-0">
                {piece.arabic}
              </ArabicText>
              <ArabicText size="tiny">{piece.grammar.join(' · ')}</ArabicText>
            </li>
          ))}
        </ul>
      )}

      {(word.root || word.type || word.case || word.sign) && (
        <div className="grid grid-cols-2 gap-2.5 type-small">
          {word.root && <Detail label="Root" value={word.root} arabic />}
          {word.type && <Detail label="Type" value={typeLabel(word.type)} arabic />}
          {word.case && <Detail label="Case" value={caseLabel(word.case)} arabic />}
          {word.sign && <Detail label="Sign" value={signLabel(word.sign)} arabic />}
        </div>
      )}

      {word.reason && (
        <Panel label="Proof (الدليل)" accent>{word.reason}</Panel>
      )}
      {word.notes && <Panel label="Notes">{word.notes}</Panel>}

      {/* The root is a doorway, not just a fact: from here the same root
          can be conjugated, defined, or found in the Qur'an. */}
      {!word.root && (
        <p className="type-small text-[var(--text-faint)]">
          No root: particles and pronouns are not built from one.
        </p>
      )}
      {word.root && onGo && (
        <RootActions root={word.root} onGo={onGo} exclude={exclude} className="pt-0.5" />
      )}
    </div>
  )
}

function Detail({ label, value, arabic }) {
  return (
    <div className="rounded-[var(--radius-sm)] p-3 bg-[var(--surface-hi)]">
      <div className="text-[var(--text-faint)] type-tiny uppercase tracking-wide mb-1">{label}</div>
      {arabic
        ? <ArabicText className="text-[var(--text)]">{value}</ArabicText>
        : <div className="text-[var(--text)]">{value}</div>}
    </div>
  )
}

function Panel({ label, accent = false, children }) {
  return (
    <div
      className="mt-1 p-3 rounded-[var(--radius-sm)] type-small text-[var(--text)]"
      style={{
        background: accent
          ? 'color-mix(in srgb, var(--c) 10%, transparent)'
          : 'var(--surface-hi)',
      }}
    >
      {/* text-dim, not text-faint: this label sits on a tinted panel, where the
          fainter token drops below the 4.5:1 contrast minimum. */}
      <div className="text-[var(--text-dim)] type-tiny uppercase tracking-wide mb-1">{label}</div>
      {children}
    </div>
  )
}
