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

import { isQuranic, joinedOn, seatSmallAlef } from '../lib/arabicText'
import { roleVar } from '../lib/roleColors'
import { kids, pieces, rows, share, splitConnectors } from '../lib/tarkeebLayout'
import { useRail } from '../lib/useRail'
import { colorFor } from '../theme'

import ArabicText from './ui/ArabicText'
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
      <div className="tk-roles">
        {(kids(node) ?? pieces(node)).map((piece, index) => (
          <Fragment key={index}>
            {index > 0 && <span className="tk-plus" aria-hidden="true">+</span>}
            <div
              className={`tk-role${piece.gap ? ' tk-gap' : ''}${piece.raw_wording ? ' tk-raw' : ''}`}
              style={{ flexGrow: share(piece), '--tone': roleVar(piece.tone) }}
            >
              {/* Tooltip is a no-op without text, so every role can pass through
                  it, only the roles with a `detail` (currently the ghair-عامل
                  connectives) end up hoverable. */}
              <Tooltip text={piece.detail}>{piece.role}</Tooltip>
            </div>
          </Fragment>
        ))}
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

/** The written words, each as the run of columns cut from it: [{ from, to }], in column order. */
const writtenWords = (written) =>
  written.reduce((runs, word, index) => {
    const last = runs.at(-1)
    if (last && written[last.from] === word) last.to = index
    else runs.push({ from: index, to: index })
    return runs
  }, [])

export default function TarkeebDiagram({ words, written, tree, unwritten }) {
  const [mode, setMode] = useState('split')
  const [dots, setDots] = useState([])
  const { strip, ends, measure, page } = useRail(`${words?.join(' ')}|${mode}`)
  const split = useMemo(
    () => (tree && words?.length ? splitConnectors(words, tree, written) : null),
    [words, written, tree],
  )
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
  if (!tree || !words?.length) return null

  const canSplit = split.words.length > words.length
  const shown = mode === 'split' && canSplit ? split : { words, written: written ?? words.map((_, i) => i), tree }
  const levels = rows(shown.tree, shown.words.length)
  const cells = writtenWords(shown.written)
  // the columns of a written word cut into pieces
  const cut = new Set(cells.flatMap(({ from, to }) => (to > from ? Array.from({ length: to - from + 1 }, (_, k) => from + k) : [])))
  const goTo = (index) => {
    const view = strip.current
    const word = view.querySelectorAll('.tk-word')[index]
    view.scrollTo({ left: word.offsetLeft - (view.clientWidth - word.offsetWidth) / 2, behavior: 'smooth' })
  }

  return (
    <div>
      {canSplit && (
        <div className="flex items-center justify-end gap-2 pb-3 flex-wrap">
          {/* The caption reuses the connective's own term text from the tree
              instead of a wording invented here, no new Arabic in this file. */}
          <ArabicText size="sm" className="text-[var(--text-faint)]">{split.terms.join(' / ')}</ArabicText>
          <Segmented
            label="Show the connective as its own column, or merged with the word after it"
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
            // a piece of a written word is only as wide as it needs, so the word's pieces sit close
            gridTemplateColumns: `${shown.words.map((_, index) => (cut.has(index) ? 'max-content' : 'minmax(max-content, 1fr)')).join(' ')} ${NAME_COLUMN}`,
          }}
        >
          {cells.map(({ from, to }) => {
            const word = shown.words[from]
            // The mark comes from the API, so no text stands for "not written" here.
            const missing = unwritten && word === unwritten.mark
            // فَـ لْـ يَصُمْهُ: one written word is drawn once across its pieces' columns,
            // its pieces close and joined as the script joins them, on one line
            const pieces = shown.words.slice(from, to + 1)
            return (
              <div
                className={`tk-word${missing ? ' tk-unwritten' : ''}${to > from ? ' tk-written' : ''}`}
                key={`word-${from}`}
                style={{ gridColumn: `${from + 1} / ${to + 2}` }}
              >
                <Tooltip text={missing ? unwritten.note : undefined}>
                  <span>
                    {to > from
                      ? pieces.map((text, k) => <span key={k} className="tk-cut">{seatSmallAlef(k < pieces.length - 1 ? joinedOn(text) : text)}</span>)
                      : seatSmallAlef(word)}
                  </span>
                </Tooltip>
              </div>
            )
          })}

          {levels.map(({ level, groups, threads }) => (
            <Fragment key={level}>
              {groups.map((node) => (
                <Bracket
                  key={`${level}-${node.from}`}
                  node={node}
                  atEdge={node.to === shown.words.length - 1}
                  style={{ gridRow: level + 1, gridColumn: `${node.from + 1} / ${node.to + 2}` }}
                />
              ))}
              {/* a piece of a joined word has no thread: the word is drawn across its columns, not over each */}
              {threads.filter((word) => !cut.has(word)).map((word) => (
                <div
                  className="tk-thread"
                  data-level={level}
                  key={`thread-${level}-${word}`}
                  style={{ gridRow: level + 1, gridColumn: word + 1 }}
                  aria-hidden="true"
                />
              ))}
            </Fragment>
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
