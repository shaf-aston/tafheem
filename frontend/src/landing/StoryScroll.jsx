import { useRef } from 'react'

import { roleVar } from '../lib/roleColors'
import { loadDemo } from './loadDemo.js'
import useScrollProgress from './useScrollProgress.js'

// Every single word of the demo sentence with the role and colour the real
// analysis gave it, in reading order.
function leaves(node, out = []) {
  if (node.children?.length) node.children.forEach((c) => leaves(c, out))
  else if (node.word != null) out[node.word] = { role: node.role, tone: node.tone }
  return out
}
const demo = loadDemo()
const DEMO_WORDS = leaves(demo.tree).map((l, i) => ({ word: demo.words[i], ...l }))

// Four steps, each a numbered line on the left and an Arabic panel on the
// right. Accent is the colour of the tool that step is actually about.
const STEPS = [
  {
    title: 'Type a sentence',
    body: 'Plain typed Arabic, harakat optional. The grammar engine assigns case the way a governor would.',
    accent: 'var(--nahw)',
    arabic: 'كَتَبَ الطَّالِبُ رِسَالَةً',
    caption: 'typed sentence, ready to parse',
  },
  {
    title: 'See the grammar',
    body: "Full i'raab, role by role, colour-coded, with a tarkeeb bracket tree underneath.",
    accent: 'var(--nahw)',
    words: true,
    caption: 'every word tagged with its role',
  },
  {
    title: 'Recite and be checked',
    body: 'Speak an ayah. Every word is heard back, mistakes flagged where they happened.',
    accent: 'var(--quran)',
    arabic: 'بِسْمِ ٱللَّهِ',
    caption: '1,950 real recitations, scored word by word',
  },
  {
    title: 'Trace the root',
    body: "One root, four classical dictionaries, one search. Ibn Faris's origin sense, in English.",
    accent: 'var(--dict)',
    arabic: 'ك ت ب ← جَمْعُ شَيْءٍ إِلَى شَيْءٍ',
    caption: '"gathering one thing to another", Ibn Faris',
  },
]

// The active step follows how far the reader is through the track, in both
// directions: scrolling back up relights the earlier steps. A latching
// in-view hook can only ever move forward, which is why it is not used here.
export default function StoryScroll() {
  const trackRef = useRef(null)
  const progress = useScrollProgress(trackRef)
  const active = Math.min(STEPS.length - 1, Math.floor(progress * STEPS.length))

  return (
    <section className="story" id="story">
      <div className="story-track" ref={trackRef}>
        <div className="story-sticky">
          <div className="story-grid">
            <div className="story-steps">
              {STEPS.map((s, i) => (
                <div
                  key={s.title}
                  className={`story-step${i === active ? ' active' : ''}`}
                  style={{ '--accent': s.accent }}
                >
                  <span className="num mono">{String(i + 1).padStart(2, '0')}</span>
                  <h3>{s.title}</h3>
                  <p>{s.body}</p>
                </div>
              ))}
            </div>
            <div className="story-visual">
              {STEPS.map((s, i) => (
                <div key={s.title} className={`story-panel${i === active ? ' active' : ''}`}>
                  <div>
                    {s.words ? (
                      <p className="story-words" lang="ar" dir="rtl">
                        {DEMO_WORDS.map((w) => (
                          <span className="story-word" key={w.word} style={{ '--tone': roleVar(w.tone) }}>
                            <span className="arabic">{w.word}</span>
                            <span className="story-role arabic">{w.role}</span>
                          </span>
                        ))}
                      </p>
                    ) : (
                      <p className="arabic" lang="ar" dir="rtl" style={{ color: s.accent }}>{s.arabic}</p>
                    )}
                    <p className="tagline">{s.caption}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
