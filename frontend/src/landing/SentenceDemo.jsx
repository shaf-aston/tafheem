import { useEffect, useMemo, useRef, useState } from 'react'

import TarkeebDiagram from '../components/TarkeebDiagram'
import { rows } from '../lib/tarkeebLayout'
import { loadDemo } from './loadDemo.js'
import useScrollProgress from './useScrollProgress.js'

const GROW_END = 0.14
const PHONE = '(max-width: 600px)'

// Scrolling breaks one sentence down: the whole line, then its words, then each
// join of words into phrases, until the full tarkeeb tree is on screen.
export default function SentenceDemo({ demo = loadDemo() }) {
  const { words, tree } = demo
  const trackRef = useRef(null)
  const rootRef = useRef(null)
  const progress = useScrollProgress(trackRef)
  const [reduced] = useState(() => matchMedia('(prefers-reduced-motion: reduce)').matches)
  const [phone, setPhone] = useState(() => matchMedia(PHONE).matches)

  useEffect(() => {
    const mq = matchMedia(PHONE)
    const on = () => setPhone(mq.matches)
    mq.addEventListener('change', on)
    return () => mq.removeEventListener('change', on)
  }, [])

  const maxLevel = useMemo(() => Math.max(...rows(tree, words.length).map((r) => r.level)), [tree, words])
  const stages = maxLevel + 2
  const stage = reduced
    ? stages - 1
    : Math.min(stages - 1, Math.floor(Math.max(0, (progress - GROW_END) / (1 - GROW_END)) * stages))
  const grow = reduced ? 1 : Math.min(1, progress / GROW_END)

  useEffect(() => {
    rootRef.current.querySelectorAll('[data-level]').forEach((el) => {
      el.toggleAttribute('data-on', Number(el.dataset.level) <= stage - 1)
    })
  }, [stage])

  // On a phone the map is wider than the screen, so scrolling the page also
  // carries the view along it: from the sentence's start (right) to its end.
  useEffect(() => {
    const view = rootRef.current.querySelector('.tk-scroller')
    if (!phone || !view) return
    const t = Math.min(1, Math.max(0, (progress - GROW_END) / (1 - GROW_END)))
    view.scrollLeft = -(view.scrollWidth - view.clientWidth) * t
  }, [progress, phone])

  const caption = stage === 0
    ? 'One sentence.'
    : stage === 1
      ? 'Split into words.'
      : stage < stages - 1
        ? `Words join into phrases: step ${stage - 1} of ${maxLevel}.`
        : 'The whole sentence, mapped.'

  return (
    <section className="pin" id="deep-dive">
      <div className="pin-track" ref={trackRef}>
        <div className="pin-sticky">
          <p className="pin-label label">Scroll to expand</p>
          <div className="sd-frame" style={{ '--grow': grow }}>
            <p className="sd-sentence arabic" lang="ar" dir="rtl" data-hidden={stage > 0 || undefined}>
              {words.join(' ')}
            </p>
            <div className="sd-diagram" ref={rootRef} data-shown={stage > 0 || undefined}>
              <TarkeebDiagram words={words} tree={tree} />
            </div>
          </div>
          <div className="pin-caption">
            <ol className="pin-dots" aria-hidden="true">
              {Array.from({ length: stages }, (_, i) => <li key={i} data-on={i <= stage || undefined} />)}
            </ol>
            <h3>{caption}</h3>
          </div>
        </div>
      </div>
    </section>
  )
}
