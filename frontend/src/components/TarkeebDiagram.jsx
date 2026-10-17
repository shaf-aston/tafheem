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
import { Fragment, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'

import { isQuranic, joinedOn, joinsOn, seatSmallAlef } from '../lib/arabicText'
import { roleVar } from '../lib/roleColors'
import { cells, fold, foldRows, hiddenWords, rows, runs, threadSpans, tones } from '../lib/tarkeebLayout'
import { useRail } from '../lib/useRail'

import Tooltip from './ui/Tooltip'

// Rows of names shown before the rest fold behind "more rows": every book example
// fits in four; a long ayah's widest joins wait for a tap.
const ROWS_SHOWN = 4

/**
 * One brace, the row of names above it, and the name of the unit itself.
 *
 * Every name hangs under its own brace's stem, so it stays beside the words it
 * names: the brace already says "these join", so no "=" or "+" says it again.
 */
function Bracket({ node, style }) {
  // roleVar is the word grid's own lookup, so one role is one colour in both.

  return (
    <div className="tk-group" data-level={node.level} style={style}>
      {/* each name over its own words' columns: the row is a subgrid of the chart's */}
      <div className="tk-roles">
        {cells(node).map((cell, index) => {
          // one word holding several names (فعل، فاعل) forks to them, one line to each;
          // names sharing several columns (فَ and the answer it ties) stand side by side
          const forked = cell.roles.length > 1 && cell.from === cell.to
          return (
            <div
              key={index}
              className={`tk-cell${forked ? ' tk-forked' : ''}`}
              style={{ gridColumn: `${cell.from - node.from + 1} / ${cell.to - node.from + 2}` }}
            >
              {/* the line down from the word to the split: its own row, as tall as the row has room */}
              {forked && <span className="tk-stem" style={{ gridColumn: `1 / ${cell.roles.length + 1}` }} aria-hidden="true" />}
              {cell.roles.map((piece, k) => (
                <div className="tk-branch" key={k}>
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
              ))}
            </div>
          )
        })}
      </div>
      <div className="tk-brace" style={{ '--tone': roleVar(node.tone) }} />
      {node.label && <div className="tk-name" style={{ '--tone': roleVar(node.tone) }}>{node.label}</div>}
    </div>
  )
}

/**
 * How much the chart shrinks to fit its box, 1 when it already fits. Read at
 * full size: the stylesheet floors it at theme.json's arabic.chart-fit-min,
 * and a chart still wider than that scrolls.
 */
function fitChart(view, chart) {
  chart.style.removeProperty('--tk-fit')
  chart.style.setProperty('--tk-fit', String(Math.min(1, view.clientWidth / chart.scrollWidth)))
}

/**
 * Where a word's middle sits along the strip, in the strip's own
 * scrolled pixels. Read off the screen rather than offsetLeft, which inside the
 * shrunk chart counts unshrunk pixels and put every dot and jump off by the
 * shrink.
 */
function along(view, word) {
  const box = word.getBoundingClientRect()
  return box.left - view.getBoundingClientRect().left + view.scrollLeft + box.width / 2
}

/** Where each written word sits along the strip, and whether it is in view: the dots. */
function placeDots(view) {
  const width = view.scrollWidth
  return [...view.querySelectorAll('.tk-word')].map((word) => {
    const middle = along(view, word)
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
 * `mode` is 'split' (a column per piece) or 'merged' (each written word whole); the
 * choice is made beside the chart's header (TarkeebTools), not on the chart.
 * `whole` draws every row, for the larger view; otherwise the rows past
 * ROWS_SHOWN wait behind a "more rows" button.
 */
export default function TarkeebDiagram({ tarkeeb, mode = 'split', whole = false, onWord }) {
  const { words, written, tree, unwritten } = tarkeeb
  const [dots, setDots] = useState([])
  const { strip, ends, measure, page } = useRail(`${words.join(' ')}|${mode}`)
  const grid = useRef(null)
  const [unfolded, setUnfolded] = useState(whole)
  const merged = useMemo(() => (tree ? fold({ words, written, tree }) : null), [words, written, tree])
  const settle = useCallback(() => {
    measure()
    if (strip.current) setDots(placeDots(strip.current))
  }, [measure, strip])
  const refit = useCallback(() => {
    const view = strip.current
    if (!view || !grid.current) return
    fitChart(view, grid.current)
    view.scrollTo({ left: view.scrollWidth })
    settle()
  }, [strip, settle])
  // A diagram wider than its box opens on the sentence's first word, which is
  // on the right. The scroller itself is left-to-right, so left to itself it
  // opened on the last word, and on a phone that was all anyone saw.
  useLayoutEffect(() => {
    refit()
    document.fonts?.ready.then(refit)
  }, [words, tree, mode, unfolded, refit])
  // A box that changes width (a phone turned, a sidebar opened) fits again.
  useEffect(() => {
    const view = strip.current
    if (!view || typeof ResizeObserver === 'undefined') return undefined
    let width = view.clientWidth
    const watch = new ResizeObserver(() => {
      if (view.clientWidth === width) return
      width = view.clientWidth
      refit()
    })
    watch.observe(view)
    return () => watch.disconnect()
  }, [strip, refit])
  if (!tree || !words.length) return null

  const shown = mode === 'merged' ? merged : tarkeeb
  const { shown: levels, more } = foldRows(rows(shown.tree, shown.words.length), unfolded ? Infinity : ROWS_SHOWN)
  const spans = runs(shown.words, shown.written)
  const hidden = hiddenWords(shown.tree)
  // each word's underline in its own name's colour, so the eye pairs them
  const tone = tones(shown.tree)
  const goTo = (index) => {
    const view = strip.current
    const middle = along(view, view.querySelectorAll('.tk-word')[index])
    view.scrollTo({ left: middle - view.clientWidth / 2, behavior: 'smooth' })
  }

  return (
    <div>
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
          ref={grid}
          className="tk-grid"
          style={{
            // every word takes only the width it needs, so a long sentence pages less
            gridTemplateColumns: `repeat(${shown.words.length}, max-content)`,
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
                // a written word opens in the dictionary, the same search as typing it there
                {...(onWord && !missing && {
                  role: 'button',
                  tabIndex: 0,
                  title: 'Look this word up',
                  onClick: () => onWord(pieces.join('').replaceAll('ـ', '')),
                  onKeyDown: (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault()
                      onWord(pieces.join('').replaceAll('ـ', ''))
                    }
                  },
                })}
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
      {more > 0 && (
        <button type="button" className="tk-more press tap" onClick={() => setUnfolded(true)}>
          <span aria-hidden="true">▸</span> {more} more {more === 1 ? 'row' : 'rows'}
        </button>
      )}
    </div>
  )
}
