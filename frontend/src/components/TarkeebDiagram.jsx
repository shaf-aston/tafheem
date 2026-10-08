/**
 * The tarkeeb of an ayah, drawn as the bracket diagram a Nahw book uses.
 *
 * Words across the top; each row below is one level of joining, with a brace
 * under the words it gathers and the name of the unit on its left. A word not
 * yet joined keeps a thread running down to the row where it is named.
 *
 * Nothing here decides where anything goes, tarkeebLayout works that out from
 * the tree's shape, and nothing about position is stored in the data. Colours
 * come from theme.json as `--role-<tone>`; this file names no colour of its own.
 */
import { Fragment, useCallback, useLayoutEffect, useMemo, useState } from 'react'

import { isQuranic, joinedOn, joinsOn, seatSmallAlef } from '../lib/arabicText'
import { roleVar } from '../lib/roleColors'
import { cells, fold, hiddenWords, rows, runs, threadSpans, tones } from '../lib/tarkeebLayout'
import { useRail } from '../lib/useRail'
import { colorFor } from '../theme'

import Segmented from './ui/Segmented'
import Tooltip from './ui/Tooltip'

const NAME_COLUMN = '11rem'
const GHAIR_AAMIL_ACCENT = colorFor('role', 'ghair_aamil')
const MODES = [
  { id: 'merged', label: 'Merged' },
  { id: 'split', label: 'Split' },
]

/**
 * One brace, the row of names above it, and the name of the unit itself.
 *
 * The name normally sits on the brace's left, in the gutter column the grid
 * keeps for it. Only a group reaching the leftmost word has that gutter beside
 * it though: any other group's left is another group, so `atEdge` is false and
 * the name drops under its own brace instead of being drawn over the neighbour.
 */
function Bracket({ node, atEdge, style }) {
  // roleVar is the word grid's own lookup, so one role is one colour in both.
  const name = node.label && (
    <div className="tk-name">
      {/* RTL reading order: the brace, then "=", then the name on the left. */}
      <span className="tk-eq" aria-hidden="true">=</span>
      <span>{node.label}</span>
    </div>
  )

  return (
    <div className="tk-group" data-level={node.level} style={style}>
      {/* each name over its own words' columns: the row is a subgrid of the chart's */}
      <div className="tk-roles">
        {cells(node).map((cell, index) => {
          // one word holding several names (فعل + فاعل) forks to them, one line to each;
          // names sharing several columns (فَ and the answer it ties) are read in order with a "+"
          const forked = cell.roles.length > 1 && cell.from === cell.to
          return (
            <div
              key={index}
              className={`tk-cell${index > 0 ? ' tk-after' : ''}${forked ? ' tk-forked' : ''}`}
              style={{ gridColumn: `${cell.from - node.from + 1} / ${cell.to - node.from + 2}` }}
            >
              {cell.roles.map((piece, k) => (
                <Fragment key={k}>
                  {k > 0 && !forked && <span className="tk-plus" aria-hidden="true">+</span>}
                  <div className="tk-branch">
                    <div
                      className={`tk-role${piece.gap ? ' tk-gap' : ''}${piece.raw_wording ? ' tk-raw' : ''}`}
                      style={{ '--tone': roleVar(piece.tone) }}
                    >
                      {/* Tooltip is a no-op without text, so every role can pass through
                          it, only the roles with a `detail` end up hoverable. */}
                      <Tooltip text={piece.detail}>{piece.role}</Tooltip>
                    </div>
                    {/* the pronoun a doer stands for, which is not written anywhere */}
                    {piece.pronoun && <div className="tk-says">{piece.pronoun}</div>}
                  </div>
                </Fragment>
              ))}
            </div>
          )
        })}
      </div>
      <div className="tk-brace" style={{ '--tone': roleVar(node.tone) }}>{atEdge && name}</div>
      {!atEdge && name}
    </div>
  )
}

/** Where each written word sits along the strip, and whether it is in view: the dots. */
function placeDots(view) {
  const width = view.scrollWidth
  return [...view.querySelectorAll('.tk-word')].map((word) => {
    const middle = word.offsetLeft + word.offsetWidth / 2
    return {
      left: (middle / width) * 100,
      on: middle >= view.scrollLeft && middle <= view.scrollLeft + view.clientWidth,
      label: word.textContent,
    }
  })
}

/**
 * `tarkeeb` is the API's chart, as every tab gets it: { words, written, tree, unwritten },
 * the words already cut into their pieces (فَـ إِذًا), `written` naming each piece's word.
 */
export default function TarkeebDiagram({ tarkeeb }) {
  const { words, written, tree, unwritten } = tarkeeb
  const [mode, setMode] = useState('split')
  const [dots, setDots] = useState([])
  const { strip, ends, measure, page } = useRail(`${words.join(' ')}|${mode}`)
  const merged = useMemo(() => (tree ? fold({ words, written, tree }) : null), [words, written, tree])
  const settle = useCallback(() => {
    measure()
    if (strip.current) setDots(placeDots(strip.current))
  }, [measure, strip])
  // A diagram wider than its box opens on the sentence's first word, which is
  // on the right. The scroller itself is left-to-right, so left to itself it
  // opened on the last word, and on a phone that was all anyone saw.
  useLayoutEffect(() => {
    const view = strip.current
    if (!view) return
    view.scrollTo({ left: view.scrollWidth })
    settle()
    document.fonts?.ready.then(settle)
  }, [words, tree, mode, strip, settle])
  if (!tree || !words.length) return null

  const canSplit = merged.words.length < words.length
  const shown = mode === 'merged' ? merged : tarkeeb
  const levels = rows(shown.tree, shown.words.length)
  const spans = runs(shown.words, shown.written)
  const hidden = hiddenWords(shown.tree)
  // each word's underline in its own name's colour, so the eye pairs them
  const tone = tones(shown.tree)
  // the columns of a written word cut into pieces
  const cut = new Set(spans.flatMap(({ from, to }) => (to > from ? Array.from({ length: to - from + 1 }, (_, k) => from + k) : [])))
  const goTo = (index) => {
    const view = strip.current
    const word = view.querySelectorAll('.tk-word')[index]
    view.scrollTo({ left: word.offsetLeft - (view.clientWidth - word.offsetWidth) / 2, behavior: 'smooth' })
  }

  return (
    <div>
      {canSplit && (
        <div className="flex justify-end pb-3">
          <Segmented
            label="Show each piece written onto a word in its own column, or the written word whole"
            value={mode}
            onChange={setMode}
            accent={GHAIR_AAMIL_ACCENT}
            options={MODES}
          />
        </div>
      )}
      {/* Horizontal scroll region: keyboard-focusable so a non-mouse user can
          reach it. The focus ring comes from the global focus-visible rule
          in styles/base.css, which already covers [tabindex]. */}
      {/* Named by its sentence: a page of worked examples has several of these,
          and same-named regions are one region to a screen reader. */}
      <div className="tk-frame">
      {dots.length > 1 && !(ends.start && ends.end) && (
        <div className="tk-dots">
          {dots.map((dot, index) => (
            <button
              type="button"
              key={index}
              className="tk-dot"
              style={{ left: `${dot.left}%` }}
              data-on={dot.on || undefined}
              aria-label={`Go to ${dot.label}`}
              onClick={() => goTo(index)}
            />
          ))}
        </div>
      )}
      <button type="button" className="rail-arrow rail-arrow-l" aria-label="Further into the sentence" disabled={ends.start} onClick={() => page(-1)}>
        &#8249;
      </button>
      <div ref={strip} onScroll={settle} className="tk-scroller" data-script={isQuranic(shown.words.join(' ')) ? 'quran' : undefined} tabIndex={0} role="region" aria-label={`Tarkeeb of ${shown.words.join(' ')}, scroll sideways to see the rest`}>
        <div
          className="tk-grid"
          style={{
            // a piece of a written word, and an unwritten word tucked by its verb, take only the width they need
            gridTemplateColumns: `${shown.words.map((_, index) => (cut.has(index) || hidden.has(index) ? 'max-content' : 'minmax(max-content, 1fr)')).join(' ')} ${NAME_COLUMN}`,
          }}
        >
          {spans.map(({ from, to }) => {
            const word = shown.words[from]
            // The tree marks the leaves not written, so no text stands for "not written" here.
            const missing = hidden.has(from)
            // فَـ لْـ يَصُمْهُ: one written word drawn across its pieces' columns, each piece
            // over its own name, the joining written as the tatweel in the text
            const pieces = shown.words.slice(from, to + 1)
            return (
              <div
                className={`tk-word${missing ? ' tk-unwritten' : ''}${to > from ? ' tk-written' : ''}`}
                key={`word-${from}`}
                style={{ gridColumn: `${from + 1} / ${to + 2}`, '--tone': roleVar(tone[from]) }}
              >
                {to > from ? (
                  pieces.map((text, k) => {
                    // each piece underlined in its own name's colour; وَ joins nothing after it,
                    // so it stands apart, فَـ and لْـ end in the tatweel that joins them to the next piece.
                    const joins = k < pieces.length - 1 && joinsOn(text)
                    return (
                      <span key={k} className="tk-cut" style={{ gridColumn: k + 1, '--tone': roleVar(tone[from + k]) }}>
                        <span className="tk-text">{seatSmallAlef(joins ? joinedOn(text) : text)}</span>
                      </span>
                    )
                  })
                ) : (
                  <Tooltip text={missing ? unwritten?.note : undefined}>
                    <span className="tk-text">{seatSmallAlef(word)}</span>
                  </Tooltip>
                )}
              </div>
            )
          })}

          {levels.map(({ level, groups }) => (
            <Fragment key={level}>
              {groups.map((node) => (
                <Bracket
                  key={`${level}-${node.from}`}
                  node={node}
                  atEdge={node.to === shown.words.length - 1}
                  style={{ gridRow: level + 1, gridColumn: `${node.from + 1} / ${node.to + 2}` }}
                />
              ))}
            </Fragment>
          ))}
          {/* a word named further down than the row under it has a line running down to its name */}
          {threadSpans(levels).map(({ word, from, to }) => (
            <div
              className="tk-thread"
              key={`thread-${word}-${from}`}
              style={{ gridRow: `${from + 1} / ${to + 2}`, gridColumn: word + 1 }}
              aria-hidden="true"
            />
          ))}
        </div>
      </div>
      <button type="button" className="rail-arrow rail-arrow-r" aria-label="Back to the start of the sentence" disabled={ends.end} onClick={() => page(1)}>
        &#8250;
      </button>
      </div>
    </div>
  )
}
