import { useRef } from 'react'

import MicMark from '../components/ui/MicMark'
import { roleVar } from '../lib/roleColors'
import theme from '../theme.json'
import GovPanel from './GovPanel.jsx'
import links from './links.json'
import RootPanel from './RootPanel.jsx'
import { DEMO_WORDS, GOVERNS } from './storyData.js'
import useScrollProgress from './useScrollProgress.js'

// The ayah of step 3, and the one word the demo flags.
const AYAH = ['بِسْمِ', 'ٱللَّهِ', 'ٱلرَّحْمَٰنِ', 'ٱلرَّحِيمِ']
const FLAGGED = 2

const CHIPS = ['إعراب كامل', 'harakat optional', 'colour by role']

const BARS = Array.from({ length: Number(theme.landing['wave-bars']) }, (_, i) => ({
  i,
  h: (0.5 + 0.5 * Math.sin(i * 0.6)) * (0.35 + 0.65 * Math.abs(Math.sin(i * 1.7))),
}))

// Twelve turned spikes and two rings: the geometric star behind the stage.
const SPIKES = Array.from({ length: 12 }, (_, i) => i * 30)

const STEPS = [
  { title: 'Every word, named', to: 'nahw', accent: 'var(--role-fail)', body: 'Paste any sentence. Each word gets its role and colour in a moment, with harakat or without.' },
  { title: 'See who governs whom', to: 'nahw', accent: 'var(--role-rel)', body: 'The tool draws the governor arrows and tells you why each word takes its case.' },
  { title: 'Recite, be heard', to: 'mem?mode=recite', accent: 'var(--quran)', body: '1,950 real recitations, scored word by word. Mistakes are flagged where they happened.' },
  { title: 'Trace any root', to: 'dict', accent: 'var(--gold-hi)', body: '"gathering one thing to another", Ibn Faris. Four classical dictionaries, one search.' },
]

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
  const progress = useScrollProgress(trackRef)
  const active = Math.min(STEPS.length - 1, Math.floor(progress * STEPS.length))
  const lp = progress * STEPS.length - active
  const shown = Math.floor(lp * 1.25 * (DEMO_WORDS.length + 1))
  const govIdx = lp < 0.6 ? 0 : 1
  const ayahDone = (i) => lp * 1.2 * AYAH.length - i >= 1

  return (
    <section className="story" id="story">
      <div className="story-track" ref={trackRef}>
        <div className="story-sticky">
          <div className="story-col">
            <div className="story-rail">
              {STEPS.map((s, i) => (
                <a
                  key={s.title}
                  href={`${links.tool}/${s.to}`}
                  className={`story-pill${i === active ? ' active' : ''}`}
                  style={{ '--accent': s.accent }}
                  aria-current={i === active ? 'step' : undefined}
                >
                  {s.title}
                </a>
              ))}
            </div>

            <div className="story-stage" style={{ '--accent': STEPS[active].accent }}>
              {/* --p here, not on the track: it changes every scroll frame, and set higher
                  it would restyle the whole story each frame. */}
              <div className="story-star" aria-hidden="true" style={{ '--p': progress }}>
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

              <div className={`story-panel${active === 1 ? ' active' : ''}`}>
                <GovPanel lp={lp} govIdx={govIdx} />
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
                    role: !ayahDone(i) ? '' : i === FLAGGED ? '✗ راجِع' : '✓',
                    tone: !ayahDone(i) ? undefined : i === FLAGGED ? 'mafool' : 'fail',
                  }))}
                  cls={(i) => (ayahDone(i) ? 'on' : '')}
                />
                <p className="story-cap">{STEPS[2].body}</p>
              </div>

              <div className={`story-panel${active === 3 ? ' active' : ''}`}>
                <RootPanel lp={lp} />
                <p className="story-cap">{STEPS[3].body}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
