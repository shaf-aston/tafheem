/**
 * The tarkeeb read down a phone instead of across it: the same tree, each join a
 * heading with a coloured rail beside the words it gathers, each word on its own
 * line with its name next to it. Nothing is cut off or shrunk; a tall sentence is
 * only a longer list, which a phone scrolls naturally. A tapped word opens its
 * answer in place, under its own line.
 */
import { Fragment, useMemo } from 'react'

import { isQuranic, joinedOn, joinsOn, seatSmallAlef } from '../../../lib/text/arabicText'
import { roleVar } from '../../../lib/nahw/roleColors'
import { GAP, flat, kids, measure, pieces } from '../../../lib/nahw/tarkeebLayout'
import { compact } from '../../../lib/nahw/tarkeebCompact'

export default function TarkeebOutline({ tarkeeb, picked, onWord, detail }) {
  const layout = useMemo(() => compact(tarkeeb), [tarkeeb])
  const tree = useMemo(() => measure(tarkeeb.tree), [tarkeeb])
  // each piece's written word, so a tap on لَ in وَلَئِن opens وَلَئِن
  const spanOf = useMemo(() => {
    const at = []
    layout.spans.forEach((span) => { for (let i = span.from; i <= span.to; i += 1) at[i] = span })
    return at
  }, [layout])

  const leaf = (node, key) => {
    const span = spanOf[node.word]
    if (!span) return null
    const piece = tarkeeb.words[node.word]
    const cut = span.to > span.from
    const last = node.word === span.to
    // a word whose pieces make up another job (خبر = حرف جر + مجرور): that job first, then its pieces
    const own = pieces(node) && !flat(node) && (node.role || node.label) ? [{ role: node.role || node.label, tone: node.tone }] : []
    const names = [...own, ...(pieces(node) ?? [node]).filter((p) => p.role || p.gap)]
    const open = (e) => onWord?.(span.text, span.nth, e.currentTarget)
    const on = !span.hidden && picked === span.nth
    return (
      <li key={key} className="tko-leaf">
        <button type="button" className={`tko-row${on ? ' tko-picked' : ''}`} disabled={span.hidden || !onWord}
          onClick={open} aria-expanded={on}>
          <span className={`tko-word${span.hidden ? ' tko-unwritten' : ''}`} style={{ '--tone': roleVar(node.gap ? 'gap' : node.tone) }}>
            {seatSmallAlef(cut && !last && joinsOn(piece) ? joinedOn(piece) : piece)}
            {cut && <small className="tko-of">{span.text}</small>}
          </span>
          <span className="tko-names">
            {names.map((name, k) => (
              <span key={k} className="tko-name" style={{ '--tone': roleVar(name.gap ? 'gap' : name.tone) }}>
                {name.gap ? GAP : name.role}
                {name.pronoun && <small> ({name.pronoun})</small>}
              </span>
            ))}
          </span>
        </button>
        {on && node.word === span.from && detail}
      </li>
    )
  }

  const walk = (node, key) => {
    const children = kids(node)
    if (!children) return leaf(node, key)
    return (
      <li key={key} className="tko-group" style={{ '--tone': roleVar(node.tone) }}>
        <div className="tko-head">
          {node.role && <b>{node.role}</b>}
          {node.label && <span>{node.label}</span>}
        </div>
        <ol>{children.map((child, k) => <Fragment key={k}>{walk(child, `${key}.${k}`)}</Fragment>)}</ol>
      </li>
    )
  }

  return (
    <ol className="tko" dir="rtl" lang="ar" data-script={isQuranic(tarkeeb.words.join(' ')) ? 'quran' : undefined}
      aria-label="Tarkeeb, as a list">
      {walk(tree, 'r')}
    </ol>
  )
}
