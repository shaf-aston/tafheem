/**
 * The tarkeeb as the books draw it, packed: the words on top, every word's own name
 * straight under it, then one brace per join, smallest joins first. No thread runs
 * down from a word to a name rows away, so the chart is only as tall as the sentence
 * is deep, and it shrinks to fit its box instead of scrolling sideways.
 */
import { useCallback, useLayoutEffect, useMemo, useRef } from 'react'

import { isQuranic, joinedOn, joinsOn, seatSmallAlef } from '../../../lib/text/arabicText'
import { roleVar } from '../../../lib/nahw/roleColors'
import { compact } from '../../../lib/nahw/tarkeebCompact'

export default function TarkeebCompact({ tarkeeb, picked, onWord, fill = false, zoom = 1 }) {
  const layout = useMemo(() => compact(tarkeeb), [tarkeeb])
  const view = useRef(null)
  const grid = useRef(null)
  // fit to the box's width (and, filling a screen, its height too), never larger than full size
  const refit = useCallback(() => {
    const box = view.current
    const chart = grid.current
    if (!box || !chart) return
    chart.style.removeProperty('--tkc-fit')
    chart.style.removeProperty('--tkc-zoom')
    const wide = box.clientWidth / chart.scrollWidth
    const tall = fill ? box.clientHeight / chart.scrollHeight : 1
    chart.style.setProperty('--tkc-fit', String(Math.min(1, wide, tall)))
    // zoomed in past the fit, the reader drags the chart about instead
    if (zoom > 1) chart.style.setProperty('--tkc-zoom', String(zoom))
  }, [fill, zoom])
  useLayoutEffect(() => {
    refit()
    document.fonts?.ready.then(refit)
    const seen = new ResizeObserver(refit)
    seen.observe(view.current)
    return () => seen.disconnect()
  }, [layout, refit])

  const { columns, spans, groups } = layout
  return (
    <div ref={view} className={`tkc${fill ? ' tkc-fill' : ''}${zoom > 1 ? ' tkc-zoomed' : ''}`} data-script={isQuranic(tarkeeb.words.join(' ')) ? 'quran' : undefined}>
      <div ref={grid} className="tkc-grid" role="group" aria-label={`Tarkeeb of ${spans.map((s) => s.text).join(' ')}`}
        style={{ gridTemplateColumns: `repeat(${columns.length}, max-content)` }}>
        {spans.map((span) => {
          const pieces = tarkeeb.words.slice(span.from, span.to + 1)
          const open = (e) => onWord?.(span.text, span.nth, e.currentTarget)
          return (
            <button type="button" key={`w${span.from}`} disabled={span.hidden || !onWord}
              className={`tkc-word${span.hidden ? ' tkc-unwritten' : ''}${picked === span.nth && !span.hidden ? ' tkc-picked' : ''}`}
              style={{ gridColumn: `${span.from + 1} / ${span.to + 2}`, gridTemplateColumns: `repeat(${pieces.length}, 1fr)` }}
              onClick={open} aria-pressed={picked === span.nth}>
              {pieces.map((piece, k) => (
                <span key={k} className="tkc-cut" style={{ '--tone': roleVar(columns[span.from + k].tone) }}>
                  {seatSmallAlef(k < pieces.length - 1 && joinsOn(piece) ? joinedOn(piece) : piece)}
                </span>
              ))}
            </button>
          )
        })}
        {columns.map((column, i) => (
          <div key={`n${i}`} className="tkc-names" style={{ gridColumn: i + 1 }}>
            {column.names.map((name, k) => (
              <span key={k} className={`tkc-name${name.tone === 'gap' ? ' tkc-gap' : ''}`} style={{ '--tone': roleVar(name.tone) }}>
                {name.role}
                {name.pronoun && <small className="tkc-says">{name.pronoun}</small>}
              </span>
            ))}
          </div>
        ))}
        {groups.map((group) => (
          <div key={`g${group.id}`} className="tkc-group" data-level={group.level}
            style={{ gridColumn: `${group.from + 1} / ${group.to + 2}`, gridRow: 2 + group.level, '--tone': roleVar(group.tone) }}>
            <span className="tkc-brace" aria-hidden="true" />
            <span className="tkc-label">
              {group.role && <b>{group.role}</b>}
              {group.label && <span>{group.label}</span>}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
