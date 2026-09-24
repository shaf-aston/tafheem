import { useEffect, useRef, useState } from 'react'
import Reveal from './Reveal.jsx'
import { scrollToEl } from '../lib/scrollToEl'
import { CLIPS } from './assets/clips.js'

// Two <video> elements cross-fade through the eight app clips in a loop, like
// the prototype's arch-frame showreel. Only this section skips useInView for
// its play/pause: it's above the fold, so it should start immediately.
export default function Hero() {
  const mediaRef = useRef(null)
  const playingRef = useRef(true)
  const [playing, setPlaying] = useState(true)
  const [reduced] = useState(() => matchMedia('(prefers-reduced-motion: reduce)').matches)

  useEffect(() => {
    // StrictMode runs this effect, its cleanup, then this effect again before
    // paint. The first run's play() promise can reject *after* its cleanup
    // has already removed the elements ("interrupted by a call to pause"),
    // which used to land on the second run's state and show Pause as
    // pressed. `live` guards every setState so only the current run's async
    // callbacks can touch state.
    let live = true
    const isReduced = reduced
    const media = mediaRef.current
    const vA = document.createElement('video')
    const vB = document.createElement('video')
    ;[vA, vB].forEach((v) => {
      v.muted = true
      v.playsInline = true
      v.setAttribute('playsinline', '')
      v.preload = 'auto'
      media.insertBefore(v, media.firstChild)
    })

    let current = vA
    let next = vB
    let idx = 0

    function loadClip(v, i) {
      v.src = CLIPS[i].src
      v.poster = CLIPS[i].poster
    }

    function swapTo(i) {
      loadClip(next, i)
      next.currentTime = 0
      if (!isReduced && playingRef.current) next.play().catch(() => {})
      next.classList.add('active')
      current.classList.remove('active')
      const tmp = current
      current = next
      next = tmp
      current.onended = () => {
        idx = (idx + 1) % CLIPS.length
        swapTo(idx)
      }
    }

    loadClip(vA, 0)
    vA.classList.add('active')
    if (!isReduced) {
      vA.onended = () => {
        idx = (idx + 1) % CLIPS.length
        swapTo(idx)
      }
      const p = vA.play()
      if (p) p.catch(() => { if (live) { playingRef.current = false; setPlaying(false) } })
    }

    return () => {
      live = false
      vA.remove()
      vB.remove()
    }
  }, [reduced])

  function toggle() {
    const active = mediaRef.current.querySelector('video.active')
    if (!active) return
    const next = !playing
    setPlaying(next)
    playingRef.current = next
    if (next) active.play().catch(() => {})
    else active.pause()
  }

  return (
    <section className="hero" id="hero">
      <span className="hero-ghost arabic" lang="ar" dir="rtl" aria-hidden="true">اقرأ</span>
      <div className="hero-grid">
        <div>
          <Reveal as="p" className="eyebrow label in">Tafheem</Reveal>
          <Reveal as="h1" className="headline in">
            <span className="mask-word"><span>Read the</span></span><br />
            <span className="mask-word"><span>Qur&apos;an. Know</span></span><br />
            <span className="mask-word"><span><span className="accent">every</span> word.</span></span>
          </Reveal>
          <Reveal as="p" className="sub in">
            One root opens four classical dictionaries. One sentence unfolds into full i&apos;raab. One
            recitation gets heard, word by word. This is the app, running, right now.
          </Reveal>
          <div className="cta-row">
            <a href="#work" className="cta">See it in action</a>
            <button
              type="button"
              className="cta ghost"
              onClick={() => scrollToEl(document.getElementById('story'), 'top')}
            >
              How it works
            </button>
          </div>
        </div>
        <div>
          <div className="arch-frame" id="heroMedia" ref={mediaRef}>
            {!reduced && (
              <div className="hero-controls">
                <button
                  className="vid-btn"
                  aria-pressed={playing}
                  aria-label={playing ? 'Pause showreel' : 'Play showreel'}
                  onClick={toggle}
                >
                  {playing ? '❚❚' : '▶'}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
