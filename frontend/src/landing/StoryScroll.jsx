import { useLayoutEffect, useRef, useState } from 'react'

import MicMark from '../components/ui/MicMark'
import { roleVar } from '../lib/roleColors'
import theme from '../theme.json'
import { loadDemo } from './loadDemo.js'
import useScrollProgress from './useScrollProgress.js'

// Every word of the demo sentence with the role and colour the real analysis
// gave it, in reading order.
function leaves(node, out = []) {
  if (node.children?.length) node.children.forEach((c) => leaves(c, out))
  else if (node.word != null) out[node.word] = { role: node.role, tone: node.tone }
  return out
}
const demo = loadDemo()
const DEMO_WORDS = leaves(demo.tree).map((l, i) => ({ word: demo.words[i], ...l }))

// The two governor arrows of step 2: the particle إنّ (word 0) reaches the
// noun it puts in the accusative (word 1) and the verb reaches its object (word 4).
const GOVERNS = [
  { from: 0, to: 1, why: ['الطَّالِبَ', 'is mansub. ', 'إنَّ', ' governs it and puts it in the accusative.'] },
  { from: 3, to: 4, why: ['الرِّسَالَةَ', 'is the object of ', 'كَتَبَ', ', so it is accusative too.'] },
]

// The ayah of step 3, and the one word the demo flags.
const AYAH = ['بِسْمِ', 'ٱللَّهِ', 'ٱلرَّحْمَٰنِ', 'ٱلرَّحِيمِ']
const FLAGGED = 2

const BOOKS = [
  ['Maqayis', 'origin sense'],
  ['Lisan al-Arab', 'full entry'],
  ['Taj al-Arus', 'commentary'],
  ['Lane', 'English'],
]
const CHIPS = ['إعراب كامل', 'harakat optional', 'colour by role']

const BARS = Array.from({ length: Number(theme.landing['wave-bars']) }, (_, i) => ({
  i,
  h: (0.5 + 0.5 * Math.sin(i * 0.6)) * (0.35 + 0.65 * Math.abs(Math.sin(i * 1.7))),
}))

// Twelve turned spikes and two rings: the geometric star behind the stage.
const SPIKES = Array.from({ length: 12 }, (_, i) => i * 30)

const STEPS = [
  { title: 'Every word, named', accent: 'var(--role-fail)', body: 'Paste any sentence. Each word gets its role and colour in a moment, with harakat or without.' },
  { title: 'See who governs whom', accent: 'var(--role-rel)', body: 'The tool draws the governor arrows and tells you why each word takes its case.' },
  { title: 'Recite, be heard', accent: 'var(--quran)', body: '1,950 real recitations, scored word by word. Mistakes are flagged where they happened.' },
  { title: 'Trace any root', accent: 'var(--gold-hi)', body: '"gathering one thing to another", Ibn Faris. Four classical dictionaries, one search.' },
]

const clamp = (v) => Math.max(0, Math.min(1, v))

function Words({ list, cls = () => '' }) {
  return (
    <p className="story-words" lang="ar" dir="rtl">
      {list.map((w, i) => (
        <span className={`story-word ${cls(i)}`} key={w.word} style={w.tone !== undefined ? { '--tone': roleVar(w.tone) } : undefined}>
          <span className="arabic">{w.word}</span>
          <span className="story-role arabic">{w.role}</span>
        </span>
      ))}
    </p>
  )
}

// The active step follows how far the reader is through the track, in both
// directions, and every demo inside a step is scrubbed by how far through that
// step they are (lp, 0 to 1), so scrolling back up plays it backwards.
export default function StoryScroll() {
  const trackRef = useRef(null)
  const govRef = useRef(null)
  const progress = useScrollProgress(trackRef)
  const active = Math.min(STEPS.length - 1, Math.floor(progress * STEPS.length))
  const lp = progress * STEPS.length - active
  const [arcs, setArcs] = useState([])

  // The arrows start and end at the real word positions, so they are measured.
  useLayoutEffect(() => {
    if (active !== 1) return
    function measure() {
      const box = govRef.current
      if (!box) return
      const svg = box.querySelector('svg')
      const b = svg.getBoundingClientRect()
      if (!b.width) return
      const words = box.querySelectorAll('.story-word')
      const x = (i) => {
        const r = words[i].getBoundingClientRect()
        return r.left + r.width / 2 - b.left
      }
      setArcs(GOVERNS.map((g, k) => {
        const h = 60 + k * 6
        return `M${x(g.from)} 4C${x(g.from)} ${h} ${x(g.to)} ${h} ${x(g.to)} 4`
      }))
    }
    measure()
    window.addEventListener('resize', measure)
    return () => window.removeEventListener('resize', measure)
  }, [active])

  const shown = Math.floor(lp * 1.25 * (DEMO_WORDS.length + 1))
  const govIdx = lp < 0.6 ? 0 : 1
  const ayahDone = (i) => lp * 1.2 * AYAH.length - i >= 1

  return (
    <section className="story" id="story">
      <div className="story-track" ref={trackRef} style={{ '--p': progress }}>
        <div className="story-sticky">
          <div className="story-col">
            <div className="story-rail">
              {STEPS.map((s, i) => (
                <span
                  key={s.title}
                  className={`story-pill${i === active ? ' active' : ''}`}
                  style={{ '--accent': s.accent }}
                  aria-current={i === active ? 'step' : undefined}
                >
                  {s.title}
                </span>
              ))}
            </div>

            <div className="story-stage" style={{ '--accent': STEPS[active].accent }}>
              <div className="story-star" aria-hidden="true">
                <svg viewBox="0 0 200 200">
                  {SPIKES.map((a) => <path key={a} transform={`rotate(${a} 100 100)`} d="M100 6 L112 60 L100 100 L88 60Z" />)}
                  <circle cx="100" cy="100" r="60" />
                  <circle cx="100" cy="100" r="96" />
                </svg>
              </div>

              <div className={`story-panel${active === 0 ? ' active' : ''}`}>
                <Words list={DEMO_WORDS} cls={(i) => `${i < shown ? 'on' : ''}${i === shown - 1 && lp < 0.8 ? ' cur' : ''}`.trim()} />
                <div className="story-chips">
                  {CHIPS.map((c, i) => <span key={c} className={`story-chip${lp > 0.45 + i * 0.15 ? ' on' : ''}`}>{c}</span>)}
                </div>
                <p className="story-cap">{STEPS[0].body}</p>
              </div>

              <div className={`story-panel${active === 1 ? ' active' : ''}`} ref={govRef}>
                <Words list={DEMO_WORDS} cls={(i) => `on${GOVERNS[govIdx].from === i || GOVERNS[govIdx].to === i ? ' cur' : ''}`} />
                <svg className="story-arcs" aria-hidden="true">
                  {arcs.map((d, k) => (
                    <path
                      key={k} d={d} pathLength="1"
                      stroke={roleVar(DEMO_WORDS[GOVERNS[k].to].tone)}
                      style={{ '--d': clamp(k === 0 ? lp * 3 : (lp - 0.35) * 3) }}
                    />
                  ))}
                </svg>
                {GOVERNS.map((g, k) => (
                  <p key={k} className={`story-why${k === govIdx && lp > 0.25 ? ' on' : ''}`} style={k !== govIdx ? { display: 'none' } : undefined}>
                    <b lang="ar">{g.why[0]}</b> {g.why[1]}<b lang="ar">{g.why[2]}</b>{g.why[3]}
                  </p>
                ))}
                <p className="story-cap">{STEPS[1].body}</p>
              </div>

              <div className={`story-panel${active === 2 ? ' active' : ''}`}>
                <div className="story-mic">
                  <span className="mic-ring" aria-hidden="true" />
                  <MicMark state={active === 2 ? 'recording' : 'idle'} size={30} />
                </div>
                <div className="story-wave" aria-hidden="true">
                  {BARS.map((b) => <i key={b.i} style={{ '--h': b.h, '--i': b.i }} />)}
                </div>
                <Words
                  list={AYAH.map((word, i) => ({
                    word,
                    role: !ayahDone(i) ? '' : i === FLAGGED ? '✗ check' : '✓',
                    tone: !ayahDone(i) ? undefined : i === FLAGGED ? 'mafool' : 'fail',
                  }))}
                  cls={(i) => (ayahDone(i) ? 'on' : '')}
                />
                <p className="story-cap">{STEPS[2].body}</p>
              </div>

              <div className={`story-panel${active === 3 ? ' active' : ''}`}>
                <p className="story-root arabic" lang="ar" dir="rtl">ك ت ب</p>
                <div className="story-books">
                  {BOOKS.map(([name, what], i) => (
                    <div key={name} className={`story-book${lp > 0.08 + i * 0.1 ? ' on' : ''}`}>
                      <b>{name}</b>
                      <span>{what}</span>
                    </div>
                  ))}
                </div>
                <p className="story-cap">{STEPS[3].body}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
