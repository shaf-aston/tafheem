import { useEffect, useRef, useState } from 'react'
import { reducedMotion } from './motion.js'
import { scrollToEl } from '../lib/scrollToEl'
import links from './links.json'
import { CLIPS } from './assets/clips.js'

// Two <video> elements cross-fade through the eight app clips in a loop, like
// the prototype's arch-frame showreel. Only this section skips useInView for
// its play/pause: it's above the fold, so it should start immediately.
export default function Hero() {
  const mediaRef = useRef(null)
  const playingRef = useRef(true)
  const [playing, setPlaying] = useState(true)
  const [reduced] = useState(reducedMotion)

  useEffect(() => {
    // StrictMode runs this effect, its cleanup, then this effect again before
    // paint. The first run's play() promise can reject *after* its cleanup
    // has already removed the elements ("interrupted by a call to pause"),
    // which used to land on the second run's state and show Pause as
    // pressed. `live` guards every setState so only the current run's async
    // callbacks can touch state.
    let live = true
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
      if (!reduced && playingRef.current) next.play().catch(() => {})
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
    if (!reduced) {
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
          <p className="eyebrow label">Tafheem</p>
          <h1 className="headline">
            Read the Qur&apos;an.<br />
            <span className="accent">Understand</span><br />
            every word.
          </h1>
          <div className="cta-row">
            <a href={links.tool} className="cta">See it in action</a>
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
