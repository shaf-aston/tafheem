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
import { Fragment, useMemo, useState } from 'react'

import { roleVar } from '../lib/roleColors'
import { rows, share, splitConnectors } from '../lib/tarkeebLayout'
import { colorFor } from '../theme'

import ArabicText from './ui/ArabicText'
import Segmented from './ui/Segmented'
import Tooltip from './ui/Tooltip'
import './tarkeeb.css'

const WORD_MIN = '7rem'
const NAME_COLUMN = '11rem'
const GHAIR_AAMIL_ACCENT = colorFor('role', 'ghair_aamil')
const MODES = [
  { id: 'merged', label: 'Merged' },
  { id: 'split', label: 'Split' },
]

// The same lookup the word grid uses, so a role named here and named there can
// never end up in two different colours.
const color = (node) => roleVar(node?.tone)
const grouped = (node) => (node.children?.length ? node.children : node.parts)

/**
 * One brace, the row of names above it, and the name of the unit itself.
 *
 * The name normally sits on the brace's left, in the gutter column the grid
 * keeps for it. Only a group reaching the leftmost word has that gutter beside
 * it though: any other group's left is another group, so `atEdge` is false and
 * the name drops under its own brace instead of being drawn over the neighbour.
 */
function Bracket({ node, atEdge, style }) {
  const pieces = grouped(node)
  const inside = !node.children?.length
  const name = node.label && (
    <div className="tk-name">
      {/* RTL reading order: the brace, then "=", then the name on the left. */}
      <span className="tk-eq" aria-hidden="true">=</span>
      <span>{node.label}</span>
    </div>
  )

  return (
    <div className={`tk-group${inside ? ' tk-inside' : ''}`} data-level={node.level} style={style}>
      <div className="tk-roles">
        {pieces.map((piece, index) => (
          <Fragment key={index}>
            {index > 0 && <span className="tk-plus" aria-hidden="true">+</span>}
            <div
              className={`tk-role${piece.gap ? ' tk-gap' : ''}${piece.raw_wording ? ' tk-raw' : ''}`}
              style={{ flexGrow: share(piece), '--tone': color(piece) }}
            >
              {/* Tooltip is a no-op without text, so every role can pass through
                  it, only the roles with a `detail` (currently the ghair-عامل
                  connectives) end up hoverable. */}
              <Tooltip text={piece.detail}>{piece.role}</Tooltip>
            </div>
          </Fragment>
        ))}
      </div>
      <div className="tk-brace" style={{ '--tone': color(node) }}>{atEdge && name}</div>
      {!atEdge && name}
    </div>
  )
}

export default function TarkeebDiagram({ words, tree, unwritten, className = '' }) {
  const [mode, setMode] = useState('split')
  const split = useMemo(
    () => (tree && words?.length ? splitConnectors(words, tree) : null),
    [words, tree],
  )
  if (!tree || !words?.length) return null

  const canSplit = split.words.length > words.length
  const shown = mode === 'split' && canSplit ? split : { words, tree }
  const levels = rows(shown.tree, shown.words.length)

  return (
    <div className={className}>
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
          in index.css, which already covers [tabindex]. */}
      {/* Named by its sentence: a page of worked examples has several of these,
          and same-named regions are one region to a screen reader. */}
      <div className="tk-scroller" tabIndex={0} role="region" aria-label={`Tarkeeb of ${shown.words.join(' ')}, scroll sideways to see the rest`}>
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
                  <span>{word}</span>
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
