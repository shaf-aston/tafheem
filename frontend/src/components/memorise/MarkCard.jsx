import { useEffect, useLayoutEffect, useRef } from 'react'
import { createPortal } from 'react-dom'

import { ayahAudioUrl, play, playFrom } from '../../lib/quran/ayahAudio'
import { CHECK, MISSED, SAID, WRONG } from '../../lib/recite/follow'
import { weakParts, whyOf } from '../../lib/recite/markWhy'
import { LOOK, WAITING_LOOK } from '../../lib/recite/reciteColors'
import { PHONE, useMedia } from '../../lib/hooks/useMedia'
import config from '../../config/recite.json'

import ArabicText from '../ui/text/ArabicText'
import { hitArea } from './hitArea'

const LEAD_IN_S = config['card-lead-in-s']
const EDGE_PX = config['card-edge-px']
const WIDTH_PX = config['card-width-px']
const MAX_SHARE = config['card-phone-height-share']
const SCROLL_GAP_PX = config['card-scroll-gap-px']
const GAP = '0.5rem'
const PROBLEM = [WRONG, CHECK, MISSED]
const KEY = /^(\d+):(\d+)$/

const focus = 'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--c)]/40'
const button = `type-small inline-flex items-center gap-1.5 rounded-full border border-[var(--border-hi)] px-3 py-1.5 cursor-pointer text-[var(--text)] bg-transparent hover:bg-[var(--surface-hi)] ${focus}`
const solid = `${button} !bg-[var(--text)] !text-[var(--bg)] hover:opacity-90`

const Row = ({ label, children }) => (
  <div className="flex justify-between items-baseline gap-3 py-1.5 border-t border-[var(--border)] type-small text-[var(--text-dim)]">
    <span>{label}</span>
    <b className="font-medium text-[var(--text)] text-end">{children}</b>
  </div>
)

/** A word with the part the ear doubted underlined, when that part can be found in it. */
function WordShown({ word, weak, weakFrom, colour }) {
  const parts = weakParts(word, weak, weakFrom)
  return (
    <ArabicText size="lg" className="block text-center" style={{ color: colour }}>
      {parts
        ? <>{parts[0]}<u className="decoration-wavy decoration-[1.5px] underline-offset-8">{parts[1]}</u>{parts[2]}</>
        : word}
    </ArabicText>
  )
}

function WordBody({ mark, word }) {
  const look = LOOK[mark.state] ?? WAITING_LOOK
  const percent = mark.sure == null ? null : Math.round(mark.sure * 100)
  const shown = mark.state !== SAID && LOOK[mark.state]
  const underlined = Boolean(shown && weakParts(word, mark.weak, mark.weakFrom))
  return (
    <>
      <span
        className="type-tiny font-semibold uppercase tracking-wide rounded-full px-2 py-0.5"
        style={{ color: look.colour, background: `color-mix(in srgb, ${look.colour} 10%, transparent)` }}
      >
        {look.label}
      </span>
      <WordShown word={word} weak={shown ? mark.weak : null} weakFrom={mark.weakFrom} colour={shown ? look.colour : undefined} />
      <p className="type-body my-2 text-[var(--text)]">{whyOf(mark, underlined)}</p>
      <Row label="Page"><ArabicText size="sm">{word}</ArabicText></Row>
      <Row label="Heard">{mark.said ? <ArabicText size="sm">{mark.said}</ArabicText> : 'nothing'}</Row>
      {percent != null && (
        <div className="py-1.5 border-t border-[var(--border)] type-small" style={{ color: look.colour }}>
          <span className="text-[var(--text-dim)]">Model sure it was said right: {percent}%</span>
          <div className="h-1 rounded-sm bg-[var(--border)] overflow-hidden mt-1" role="presentation">
            <i className="block h-full bg-current" style={{ width: `${percent}%` }} />
          </div>
        </div>
      )}
    </>
  )
}

function AyahBody({ ayah, words, recite }) {
  const count = (state) => words.filter((one) => one.state === state).length
  const heard = words.map((one) => one.said).filter(Boolean).join(' ')
  // Only what there is: "2 not sure", and "All right" when nothing else is.
  const tally = [SAID, CHECK, WRONG, MISSED].filter(count).map((state) => `${count(state)} ${LOOK[state].label}`)
  const problems = words.map((one, k) => ({ one, k })).filter(({ one }) => PROBLEM.includes(one.state))
  return (
    <>
      <p className="type-body font-medium">Ayah {ayah.label}</p>
      <p className="type-small text-[var(--text-dim)] tabular-nums">
        {words.length && count(SAID) === words.length ? 'All right' : tally.join(', ') || 'Nothing reached yet'}
      </p>
      <Row label="Heard">{heard ? <ArabicText size="sm">{heard}</ArabicText> : 'nothing'}</Row>
      {problems.map(({ one, k }) => (
        <button
          key={k}
          type="button"
          onClick={() => recite.setOpen({ at: ayah.from + k })}
          className={`w-full flex justify-between items-baseline gap-3 py-1.5 border-t border-[var(--border)] cursor-pointer bg-transparent ${focus}`}
        >
          <span className="type-small" style={{ color: LOOK[one.state].colour }}>{LOOK[one.state].label}</span>
          <ArabicText size="sm">{ayah.printed[k]}</ArabicText>
        </button>
      ))}
    </>
  )
}

/**
 * What the ear made of one word, or of one ayah: one card, two modes.
 *
 * Non-modal on purpose. Reciting carries on behind it and marks keep landing,
 * so it reads `recite.words` on every render and keeps no copy of a mark.
 * Under a wide screen's word it hangs from its anchor; on a phone it docks to
 * the bottom of the screen, out of the way of the page.
 *
 * `ayah` is { key, label, from, count, printed } for the ayah the opened word
 * or number belongs to; `at` is the opened word's place on the page, or null
 * for the ayah's own card. Closes on Esc, on a press outside `anchor`, and by
 * its button.
 */
export default function MarkCard({ ayah, at, recite, anchor, onStartAt }) {
  const phone = useMedia(PHONE)
  const card = useRef(null)
  const close = useRef(null)

  useEffect(() => {
    const onKey = (event) => event.key === 'Escape' && recite.setOpen(null)
    const onPress = (event) => {
      if (!anchor.current?.contains(event.target) && !card.current?.contains(event.target)) recite.setOpen(null)
    }
    document.addEventListener('keydown', onKey)
    document.addEventListener('pointerdown', onPress)
    return () => {
      document.removeEventListener('keydown', onKey)
      document.removeEventListener('pointerdown', onPress)
    }
  }, [anchor, recite])

  // Focus goes into the card when it opens, so a keyboard reader does not have
  // to tab through a page to reach one that sits at the end of the document,
  // and back to the word or number that opened it when it closes. Not when
  // focus has already gone somewhere the reader chose.
  useEffect(() => {
    const opener = anchor.current?.querySelector('button')
    const el = card.current
    close.current?.focus({ preventScroll: true })
    return () => {
      const now = document.activeElement
      if (!now || now === document.body || el?.contains(now)) opener?.focus({ preventScroll: true })
    }
  }, [anchor])

  // On a phone the card covers the bottom of the screen: scroll the page so
  // what was tapped sits just above it.
  useEffect(() => {
    const el = card.current
    const from = anchor.current
    if (!phone || !el || !from) return
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const hidden = from.getBoundingClientRect().bottom - (el.getBoundingClientRect().top - SCROLL_GAP_PX)
    const above = from.getBoundingClientRect().top - SCROLL_GAP_PX
    const top = hidden > 0 ? hidden : Math.min(0, above)
    if (top) window.scrollBy({ top, behavior: reduced ? 'auto' : 'smooth' })
  }, [phone, anchor])

  // On a wide screen the card hangs from its anchor, centred on it, then is
  // slid back inside the page card (one edge gap in) and put above the line
  // instead when the line is in the lower half of the page and there is room.
  useLayoutEffect(() => {
    const el = card.current
    if (!el || phone) return
    const page = anchor.current?.closest('[data-recite-page]')
    const bounds = page ? page.getBoundingClientRect() : { left: 0, right: document.documentElement.clientWidth, top: 0, height: window.innerHeight }
    const from = anchor.current.getBoundingClientRect()
    el.style.translate = '0px'
    const box = el.getBoundingClientRect()
    const over = Math.max(0, bounds.left + EDGE_PX - box.left) - Math.max(0, box.right - (bounds.right - EDGE_PX))
    el.style.translate = `${over}px`
    const lower = from.top + from.height / 2 - bounds.top > bounds.height / 2
    const room = from.top - box.height - EDGE_PX > 0
    const above = lower && room
    el.style.top = above ? 'auto' : '100%'
    el.style.bottom = above ? '100%' : 'auto'
    el.style.marginTop = above ? '0' : GAP
    el.style.marginBottom = above ? GAP : '0'
  })

  const words = recite.words.slice(ayah.from, ayah.from + ayah.count)
  const mark = at == null ? null : recite.words[at]
  const owned = KEY.exec(ayah.key ?? '')
  const hear = owned ? () => play(ayahAudioUrl(Number(owned[1]), Number(owned[2]))) : null

  // The recording a mark was judged from, and where in it: the word's own
  // second, or for an ayah the latest recording among its words and the
  // earliest second any of them sits at.
  const judged = (mark ? [mark] : words).filter((one) => one.take != null)
  const take = judged.length ? Math.max(...judged.map((one) => one.take)) : null
  const recording = take != null ? recite.takeAudio(take) : undefined
  const seconds = judged.filter((one) => one.take === take && one.at != null).map((one) => one.at)
  const from = seconds.length ? Math.min(...seconds) - LEAD_IN_S : 0
  const mine = recording ? () => playFrom(recording, from) : null

  const shell = (
    <div
      ref={card}
      role="dialog"
      aria-label={mark ? `${ayah.printed[at - ayah.from]}, ${(LOOK[mark.state] ?? WAITING_LOOK).label}` : `ayah ${ayah.label}`}
      dir="ltr"
      style={phone
        ? { maxHeight: `min(${MAX_SHARE * 100}dvh, calc(100dvh - var(--layout-nav) - env(safe-area-inset-bottom, 0px) - 4rem))` }
        : { width: WIDTH_PX, marginLeft: -WIDTH_PX / 2 }}
      className={`flex flex-col bg-[var(--surface)] border border-[var(--border-hi)] rounded-[var(--radius-md)] shadow-[var(--shadow-pop)] z-[var(--layer-popover)] text-start
        ${phone
          // Above the nav and at most a share of the screen: the body scrolls, the buttons do not.
          ? 'fixed inset-x-2 bottom-[calc(var(--layout-nav)+env(safe-area-inset-bottom,0px)+0.5rem)]'
          : 'absolute left-1/2'}`}
    >
      <button
        ref={close}
        type="button"
        onClick={() => recite.setOpen(null)}
        aria-label="Close"
        className={`${hitArea} absolute top-2 end-2 z-[var(--layer-raised)] type-small text-[var(--text-faint)] px-2 rounded-full cursor-pointer bg-transparent ${focus}`}
      >
        ✕
      </button>
      <div className="min-h-0 overflow-y-auto overscroll-contain px-4 pt-4 pb-1">
        {mark
          ? <WordBody mark={mark} word={ayah.printed[at - ayah.from]} />
          : <AyahBody ayah={ayah} words={words} recite={recite} />}
      </div>
      <div className="shrink-0 flex flex-wrap gap-1.5 px-4 pt-2 pb-4">
        {hear && <button type="button" onClick={hear} className={solid}>▶ Hear it said right</button>}
        {mine && <button type="button" onClick={mine} className={button}>▶ Mine</button>}
        {onStartAt && (
          <button type="button" onClick={() => { onStartAt(mark ? at : ayah.from); recite.setOpen(null) }} className={button}>Start here</button>
        )}
      </div>
    </div>
  )
  return phone ? createPortal(shell, document.body) : shell
}
