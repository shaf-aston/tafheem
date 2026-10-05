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
import { Fragment, useLayoutEffect, useMemo, useRef, useState } from 'react'

import { isQuranic, seatSmallAlef } from '../lib/arabicText'
import { roleVar } from '../lib/roleColors'
import { kids, pieces, rows, share, splitConnectors } from '../lib/tarkeebLayout'
import { colorFor } from '../theme'

import ArabicText from './ui/ArabicText'
import Segmented from './ui/Segmented'
import Tooltip from './ui/Tooltip'

const WORD_MIN = '7rem'
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
  const inside = !kids(node)
  const name = node.label && (
    <div className="tk-name">
      {/* RTL reading order: the brace, then "=", then the name on the left. */}
      <span className="tk-eq" aria-hidden="true">=</span>
      <span>{node.label}</span>
      {/* A unit with no job of its own is said with the word it hangs on (متعلق بـخرج);
          a unit with a job keeps its detail as the hover on that job, one row up. */}
      {!node.role && node.detail && <span className="tk-said">{node.detail}</span>}
    </div>
  )

  return (
    <div className={`tk-group${inside ? ' tk-inside' : ''}`} data-level={node.level} style={style}>
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

export default function TarkeebDiagram({ words, tree, unwritten }) {
  const [mode, setMode] = useState('split')
  const scroller = useRef(null)
  const split = useMemo(
    () => (tree && words?.length ? splitConnectors(words, tree) : null),
    [words, tree],
  )
  // A diagram wider than its box opens on the sentence's first word, which is
  // on the right. The scroller itself is left-to-right, so left to itself it
  // opened on the last word, and on a phone that was all anyone saw.
  useLayoutEffect(() => {
    const view = scroller.current
    if (view) view.scrollLeft = view.scrollWidth
  }, [words, tree, mode])
  if (!tree || !words?.length) return null

  const canSplit = split.words.length > words.length
  const shown = mode === 'split' && canSplit ? split : { words, tree }
  const levels = rows(shown.tree, shown.words.length)

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
      <div ref={scroller} className="tk-scroller" data-script={isQuranic(shown.words.join(' ')) ? 'quran' : undefined} tabIndex={0} role="region" aria-label={`Tarkeeb of ${shown.words.join(' ')}, scroll sideways to see the rest`}>
        <div
          className="tk-grid"
          style={{
            gridTemplateColumns: `repeat(${shown.words.length}, minmax(${WORD_MIN}, 1fr)) ${NAME_COLUMN}`,
          }}
        >
          {shown.words.map((word, index) => {
            // The mark comes from the API, so no text stands for "not written" here.
            const missing = unwritten && word === unwritten.mark
            return (
              <div
                className={`tk-word${missing ? ' tk-unwritten' : ''}`}
                key={`word-${index}`}
                style={{ gridColumn: index + 1 }}
              >
                <Tooltip text={missing ? unwritten.note : undefined}>
                  <span>{seatSmallAlef(word)}</span>
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
              {threads.map((word) => (
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
    </div>
  )
}
