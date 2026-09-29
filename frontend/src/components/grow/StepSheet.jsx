/**
 * One step's practice card. It grows out of the circle that was tapped and
 * shrinks back into it, so the map never feels left; Escape or the scrim
 * closes it, and Tab stays inside it while it is open.
 *
 * The card holds the words, the microphone, the marks, and the scholar's words
 * on the step. Nothing about how a word is judged is decided here: lining the
 * words up and weighing the sound is lib/grow.js, what kind of step it is and
 * which ear checks it is lib/growKinds.js, and the record is the panel's.
 * A step in a locked tier, or a proposed topic that is not built yet, gets the
 * same card with the reason it is shut instead of a microphone.
 */
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { getQuranSurah } from '../../api'
import config from '../../grow.json'
import { CHECK, MISSED, SAID, WRONG } from '../../lib/follow'
import { becomesLearnt, isClean, markRecitation, nodeState, pageOf, tally } from '../../lib/grow'
import { checkStep } from '../../lib/growKinds'
import { isQuranic } from '../../lib/arabicText'
import { LOOK } from '../../lib/reciteColors'
import { sayIn } from '../../lib/say'
import { useSetting } from '../../lib/settings'
import ArabicText from '../ui/ArabicText'
import Disclosure from '../ui/Disclosure'
import ErrorAlert from '../ui/ErrorAlert'
import MicButton from '../ui/MicButton'
import { StateIcon } from './icons'

const say = sayIn('en')
const FOCUSABLE = 'button, summary, [href], [tabindex]:not([tabindex="-1"])'
const NEED = config['clean-days']
const GAP = 12

const CHIP = {
  learnt: ['grow-chip-done', say('Learnt')],
  started: ['grow-chip-now', say('In progress')],
  open: ['', say('Ready to start')],
  locked: ['', say('Locked')],
}

/** One circle of a step's days, drawn as an arc of the ring. */
const arc = (from, to) => {
  const at = (deg) => [50 + 42 * Math.cos((deg * Math.PI) / 180), 50 + 42 * Math.sin((deg * Math.PI) / 180)]
  const [x0, y0] = at(from)
  const [x1, y1] = at(to)
  return `M${x0.toFixed(1)} ${y0.toFixed(1)}A42 42 0 ${to - from > 180 ? 1 : 0} 1 ${x1.toFixed(1)} ${y1.toFixed(1)}`
}

/** One arc for each clean day a step needs, filled for each one it has. */
function DaysRing({ done }) {
  const span = 360 / NEED
  return (
    <div className="grow-days-ring" role="img" aria-label={say('Said right on {done} of {need} days', { done, need: NEED })}>
      <svg viewBox="0 0 100 100" aria-hidden="true">
        {Array.from({ length: NEED }, (_, k) => {
          const d = arc(-90 + k * span + GAP / 2, -90 + (k + 1) * span - GAP / 2)
          return (
            <g key={k}>
              <path className="grow-ring-t" d={d} />
              {done > k && <path className="grow-ring-f" d={d} />}
            </g>
          )
        })}
      </svg>
      <span>{done}/{NEED}</span>
    </div>
  )
}

/** The printed Arabic of each ayah a step names, from the Qur'an tab's own endpoint. */
function useAyahText(step) {
  const surah = step.ayahs?.length ? Number(step.ayahs[0].split(':')[0]) : null
  const found = useQuery({
    queryKey: ['quran-surah', surah],
    queryFn: () => getQuranSurah(surah),
    enabled: surah != null,
    staleTime: Infinity,
  })
  const text = useMemo(() => {
    const out = {}
    for (const ayah of found.data?.ayahs ?? []) out[`${surah}:${ayah.ayah}`] = ayah.arabic
    return out
  }, [found.data, surah])
  return { text, loading: surah != null && found.isLoading, failed: found.isError }
}

/** One honest line under a recitation. Nothing is called right that was not. */
function Verdict({ phase, marks, note }) {
  if (phase === 'idle') return <p className="grow-verdict">{say('Press the microphone, say it, then press it again.')}</p>
  if (phase === 'checking') return <p className="grow-verdict">{say('Checking each word by sound…')}</p>
  const count = tally(marks)
  const parts = []
  if (count[WRONG] + count[MISSED]) parts.push(say('{n} to fix', { n: count[WRONG] + count[MISSED] }))
  if (count[CHECK]) parts.push(say('{n} not sure', { n: count[CHECK] }))
  const clean = isClean(marks) && !note
  const text = note || (isClean(marks)
    ? say('Every word right.')
    : `${parts.join(', ')}. ${count[CHECK] && !(count[WRONG] + count[MISSED])
      ? say('The app could not tell: say it again, slowly and clearly.')
      : say('Look at the marked words and try again.')}`)
  return <p className="grow-verdict" data-ok={clean ? '' : undefined} role="status">{text}</p>
}

/**
 * The scholar's words on this step, shut until asked for. The book and the
 * chapter are one faint line under the quote: there for anyone who wants to
 * find it, not in the way of anyone who does not.
 */
function Ruling({ ruling, onGo }) {
  return (
    <Disclosure label={say('What {name} says', { name: ruling.known_as })}>
      <div className="space-y-2 pt-2">
        <ArabicText as="p" size="base" className="text-[var(--text)]">{ruling.arabic}</ArabicText>
        {ruling.english && <p className="type-small text-[var(--text-dim)] max-w-prose">{ruling.english}</p>}
        <p className="type-tiny text-[var(--text-faint)]">
          {ruling.book}, {ruling.where}
          {onGo && (
            <>
              {' · '}
              <button
                type="button"
                onClick={() => onGo('daleel', ruling.arabic.split(' ').slice(0, config['daleel-words']).join(' '))}
                className="underline underline-offset-2 hover:text-[var(--text-dim)]"
              >
                {say('Open in Daleel')}
              </button>
            </>
          )}
        </p>
      </div>
    </Disclosure>
  )
}

/** The words, the microphone, the marks and the days, for a step that is open. */
function Practice({ step, record, accent, onRecited, onGo, onBloom }) {
  const level = useSetting('reciting-level')
  const ayahText = useAyahText(step)
  const page = useMemo(() => pageOf(step, ayahText.text), [step, ayahText.text])
  // idle, checking (words back, sound being weighed), done
  const [phase, setPhase] = useState('idle')
  const [marks, setMarks] = useState(null)
  const [note, setNote] = useState('')

  async function heard({ text }, recording) {
    setNote('')
    setMarks(markRecitation(page.words, text, [], level))
    setPhase('checking')
    let sure = null
    try {
      sure = await checkStep(step, recording, text, page)
    } catch {
      sure = null
    }
    // Clean only when the sound was actually weighed for every word. A run the
    // ear could not check is shown, and never counted.
    const weighed = sure != null && page.words.every((_, i) => sure[i] != null)
    const final = markRecitation(page.words, text, sure ?? [], level)
    const clean = weighed && isClean(final)
    setMarks(final)
    setPhase('done')
    if (!weighed) setNote(say('The sound could not be checked this time, so this run is shown but not counted.'))
    if (becomesLearnt(record, step.id, clean)) onBloom()
    onRecited(clean)
  }

  const done = Math.min(record[step.id]?.cleanDays?.length ?? 0, NEED)
  const words = marks?.words ?? page.words.map((word) => ({ word, state: 'waiting' }))

  return (
    <>
      {ayahText.loading && <p className="grow-verdict">{say('Loading the ayahs…')}</p>}
      {ayahText.failed && <ErrorAlert inline title={say('Could not load the ayahs')} />}

      <p
        className="leading-loose text-center"
        dir="rtl"
        data-script={isQuranic(words.map((mark) => mark.word).join(' ')) ? 'quran' : undefined}
      >
        {words.map((mark, i) => {
          const look = LOOK[mark.state]
          const missed = mark.state === MISSED
          return (
            <span key={`${i}-${mark.word}`}>
              <ArabicText
                size="lg"
                title={look?.label}
                style={{
                  color: look?.colour,
                  ...(missed ? { border: '1px solid var(--danger)', borderRadius: '6px', padding: '0 4px' } : {}),
                }}
              >
                {mark.word}
              </ArabicText>{' '}
            </span>
          )
        })}
      </p>

      {step.meaning && <p className="grow-meaning">{step.meaning}</p>}

      <div className="grow-prac">
        <DaysRing done={done} />
        <MicButton recite accent={accent} title={say('Say it')} onHeard={heard} />
      </div>
      <Verdict phase={phase} marks={marks} note={note} />
      <p className="grow-verdict">{say('Said right on {done} of {need} days', { done, need: NEED })}</p>

      {step.ruling && <Ruling ruling={step.ruling} onGo={onGo} />}
    </>
  )
}

export default function StepSheet({ step, from, state, tier, before, record, accent, onRecited, onGo, onClosed }) {
  const box = useRef(null)
  const closeRef = useRef(null)
  const [closing, setClosing] = useState(false)
  // Bumped each time a run makes the step learnt; the key replays the bloom.
  const [bloom, setBloom] = useState(0)
  const shown = state === 'locked' ? 'locked' : nodeState([step], record)

  // Where the card grows out of and goes back to: the centre of the circle.
  const aim = useCallback(() => {
    const at = from?.isConnected ? from.getBoundingClientRect() : null
    const el = box.current
    el.style.setProperty('--dx', `${at ? at.left + at.width / 2 - innerWidth / 2 : 0}px`)
    el.style.setProperty('--dy', `${at ? at.top + at.height / 2 - innerHeight / 2 : 0}px`)
  }, [from])
  useLayoutEffect(aim, [aim])

  const close = useCallback(() => {
    aim()
    setClosing(true)
    // As long as the shrink takes, read off the token the stylesheet uses.
    const ms = Number.parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--motion-spring-ms')) || 0
    setTimeout(onClosed, ms)
  }, [aim, onClosed])

  useEffect(() => {
    closeRef.current?.focus()
    const { overflow } = document.body.style
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = overflow
      if (from?.isConnected) from.focus()
    }
  }, [from])

  useEffect(() => {
    const onKey = (event) => {
      if (event.key === 'Escape') close()
      else if (event.key === 'Tab') {
        const items = [...box.current.querySelectorAll(FOCUSABLE)].filter((el) => !el.disabled)
        const first = items[0]
        const last = items[items.length - 1]
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus() }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [close])

  const [chipClass, chipText] = step.proposed
    ? ['', `${say('Proposed')} · ${tier.title}`]
    : CHIP[shown]

  return (
    <>
      <div className="grow-scrim" data-closing={closing ? '' : undefined} onMouseDown={close} />
      <div
        ref={box}
        role="dialog"
        aria-modal="true"
        aria-labelledby="grow-sheet-title"
        className="grow-sheet"
        data-closing={closing ? '' : undefined}
      >
        <div className="grow-sh-top">
          <h3 id="grow-sheet-title">{step.title}</h3>
          <button ref={closeRef} type="button" className="grow-x" aria-label={say('Close')} onClick={close}>
            <span aria-hidden="true">×</span>
          </button>
        </div>
        <span className={`grow-chip ${chipClass}`}>{chipText}</span>

        <div key={bloom} className={`grow-stage${bloom ? ' grow-go' : ''}`} aria-hidden="true">
          <div className="grow-fan">
            {Array.from({ length: 8 }, (_, k) => <i key={k} style={{ '--a': k * 45, '--k': k }} />)}
          </div>
          <div className="grow-node grow-leaf" data-s={shown}>
            <span className="grow-in"><StateIcon state={shown} /></span>
          </div>
        </div>

        {shown === 'locked' ? (
          <>
            {step.arabic && <ArabicText as="p" size="lg" className="block text-center leading-loose">{step.arabic}</ArabicText>}
            {step.meaning && <p className="grow-meaning">{step.meaning}</p>}
            <p className="grow-note">
              {before
                ? say(step.proposed
                  ? 'Locked until {before} is learnt. Shown here as a proposal for the {tier} tier.'
                  : 'Locked until {before} is learnt.', { before: before.title, tier: tier.title })
                : say('Not open yet.')}
            </p>
          </>
        ) : (
          <Practice
            key={step.id}
            step={step}
            record={record}
            accent={accent}
            onRecited={onRecited}
            onGo={onGo}
            onBloom={() => setBloom((n) => n + 1)}
          />
        )}
      </div>
    </>
  )
}
