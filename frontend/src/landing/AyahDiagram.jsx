import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'

import { roleVar } from '../lib/roleColors'
import { reducedMotion } from './motion.js'
import './AyahDiagram.css'

// One ayah built into its tarkeeb a brace at a time, on a loop. Everything it
// shows comes from the `ayah` object; it fills whatever box it is put in and
// shrinks to fit both ways, so any section can hold it.
const FIRST_ROW = 4 // word, meaning and name take rows 1 to 3; braces start here
const tone = (t) => ({ gold: 'var(--gold-hi)', whole: 'var(--text)' })[t] ?? roleVar(t)

export default function AyahDiagram({ ayah }) {
  const { words, braces } = ayah
  // a step draws brace k; a brace with `then` takes a second step to become it
  const steps = useMemo(() => braces.flatMap((b, k) => (b.then ? [{ k }, { k, then: true }] : [{ k }])), [braces])
  // the brace that first takes each word in: its line down is drawn with that brace
  const joiner = useMemo(() => words.map((_, i) => braces.findIndex((b) => i >= b.from && i <= b.to)), [words, braces])
  const last = steps.length
  const [reduced] = useState(reducedMotion)
  const [playing, setPlaying] = useState(!reduced)
  const [step, setStep] = useState(reduced ? last : 0)
  const fitRef = useRef(null)
  const dgRef = useRef(null)

  useLayoutEffect(() => {
    const fit = fitRef.current
    const dg = dgRef.current
    const size = () => {
      dg.style.zoom = 1
      dg.style.zoom = Math.min(1, fit.clientWidth / dg.scrollWidth, fit.clientHeight / dg.scrollHeight)
    }
    const watch = new ResizeObserver(size)
    watch.observe(fit)
    document.fonts.ready.then(size)
    return () => watch.disconnect()
  }, [])

  useEffect(() => {
    if (!playing) return
    const next = setTimeout(() => setStep((s) => (s === last ? 0 : s + 1)), step === last ? ayah.endMs : ayah.stepMs)
    return () => clearTimeout(next)
  }, [playing, step, last, ayah])

  const done = steps.slice(0, step)
  const drawn = (k) => done.some((d) => d.k === k)
  // the spotlight: until the end, only the phrase being joined is lit
  const cur = step > 0 && step < last ? steps[step - 1].k : -1
  const lit = braces[cur]
  const dimWord = (i) => (lit && (i < lit.from || i > lit.to)) || undefined

  return (
    <div className="ayah-dg">
      <i className="orb" /><i className="orb" /><i className="orb" />
      <div className="fit" ref={fitRef}>
        <div
          className="dg"
          ref={dgRef}
          lang="ar"
          dir="rtl"
          role="img"
          aria-label={ayah.label}
          style={{ gridTemplateColumns: words.map((w) => (w.ghost ? 'max-content' : 'minmax(max-content, 1fr)')).join(' ') }}
        >
          {words.map((w, i) => {
            const col = { gridColumn: i + 1, '--tone': tone(w.own[1]) }
            const row = braces[joiner[i]].row
            return [
              <div key={`w${i}`} className={w.ghost ? 'wd ghost' : 'wd'} style={col} data-dim={dimWord(i)}><span className="ar">{w.ar}</span></div>,
              <div key={`g${i}`} className="gl" lang="en" dir="ltr" style={col} data-dim={dimWord(i)}>{w.gl}</div>,
              <div key={`t${i}`} className="tg" style={col} data-dim={dimWord(i)}><span className="term">{w.own[0]}</span></div>,
              row > 0 && (
                <div
                  key={`l${i}`}
                  className={drawn(joiner[i]) ? 'thread on' : 'thread'}
                  style={{ gridColumn: i + 1, gridRow: `${FIRST_ROW} / ${FIRST_ROW + row}` }}
                  data-dim={dimWord(i)}
                />
              ),
            ]
          })}
          {braces.map((b, k) => (
            <div
              key={`b${k}`}
              className={['br', drawn(k) && 'on', done.some((d) => d.k === k && d.then) && 'turned'].filter(Boolean).join(' ')}
              style={{ gridColumn: `${b.from + 1} / ${b.to + 2}`, gridRow: FIRST_ROW + b.row, '--tone': tone(b.tone) }}
              data-dim={(lit && k < cur) || undefined}
            >
              <div className="brace" />
              <div className={b.tone === 'gold' ? 'nm gold' : 'nm'}><span className="eq">=</span><span>{b.name}</span></div>
              {b.then && (
                <div className="then" style={{ '--tone': tone(b.then[1]) }}>
                  <span className="arrow" /><span className="term">{b.then[0]}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
      <p className={step === last ? 'tr on' : 'tr'}>{ayah.translation}</p>
      {!reduced && (
        <button type="button" className="ayah-play" aria-label={playing ? 'Pause' : 'Play'} onClick={() => setPlaying(!playing)}>
          {playing ? '❚❚' : '▶'}
        </button>
      )}
    </div>
  )
}
