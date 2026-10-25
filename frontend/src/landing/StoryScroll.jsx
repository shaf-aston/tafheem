import { useRef } from 'react'

import MicMark from '../components/ui/MicMark'
import { roleVar } from '../lib/nahw/roleColors'
import theme from '../config/theme.json'
import links from './links.json'
import RootPanel from './RootPanel.jsx'
import SentencePanel from './SentencePanel.jsx'
import { DEMO_WORDS, GOVERNS } from './storyData.js'
import { locate, sentencePhase } from './storyPhase.js'
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

// `weight` is how many steps' worth of scrolling a step gets. The first is two demos in
// one, the words named and then who governs whom, so it reads `body` and then `then`.
const STEPS = [
  { title: 'Every word, explained', to: 'nahw', accent: 'var(--role-fail)', weight: 2, body: 'Paste any sentence. Each word gets its role and colour in a moment, with harakat or without.', then: 'Then the tool draws the governor arrows and tells you why each word takes its case.' },
  { title: 'Recite, be heard', to: 'mem?mode=recite', accent: 'var(--quran)', body: '1,950 real recitations, scored word by word. Mistakes are flagged where they happened.' },
  { title: 'Trace any root', to: 'dict', accent: 'var(--gold-hi)', body: '"gathering one thing to another", Ibn Faris. Four classical dictionaries, one search.' },
]

const WEIGHTS = STEPS.map((s) => s.weight ?? 1)

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
  const { active, lp } = locate(progress, WEIGHTS)
  const phase = sentencePhase(lp, { words: DEMO_WORDS.length, pairs: GOVERNS })
  const naming = phase.phase === 'name'
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
                <SentencePanel
                  phase={phase}
                  notes={(
                    <div className="story-chips">
                      {CHIPS.map((c, i) => (
                        <span key={c} className={`story-chip${naming && phase.named >= Math.ceil(((i + 1) * DEMO_WORDS.length) / (CHIPS.length + 1)) ? ' on' : ''}`}>{c}</span>
                      ))}
                    </div>
                  )}
                />
                <div className="story-caps">
                  <p className={`story-cap${naming ? ' on' : ''}`} aria-hidden={!naming}>{STEPS[0].body}</p>
                  <p className={`story-cap${naming ? '' : ' on'}`} aria-hidden={naming}>{STEPS[0].then}</p>
                </div>
              </div>

              <div className={`story-panel${active === 1 ? ' active' : ''}`}>
                <div className="story-mic">
                  <span className="mic-ring" aria-hidden="true" />
                  <MicMark state={active === 1 ? 'recording' : 'idle'} size={30} />
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
                <p className="story-cap">{STEPS[1].body}</p>
              </div>

              <div className={`story-panel${active === 2 ? ' active' : ''}`}>
                <RootPanel lp={lp} />
                <p className="story-cap">{STEPS[2].body}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
