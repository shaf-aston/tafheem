/**
 * The inside of a step's card when the step is open: the words, the
 * microphone, the marks, the days and the scholar's words; or, for a posture
 * (growKinds byHand), the instruction and one Done. How a word is judged is
 * lib/grow.js (judge), which ear checks a step gets is lib/growKinds.js, and
 * the record is the panel's.
 */
import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { quranSurahQuery } from '../../api'
import config from '../../grow.json'
import { CHECK, MISSED, WAITING, WRONG } from '../../lib/follow'
import { becomesLearnt, daysOf, isLearnt, judge, pageOf, tally } from '../../lib/grow'
import { byHand, checkStep } from '../../lib/growKinds'
import { isQuranic } from '../../lib/arabicText'
import { LOOK } from '../../lib/reciteColors'
import { sayIn } from '../../lib/say'
import { useSetting } from '../../lib/settings'
import ArabicText from '../ui/ArabicText'
import Disclosure from '../ui/Disclosure'
import ErrorAlert from '../ui/ErrorAlert'
import MicButton from '../ui/MicButton'
import PrimaryButton from '../ui/PrimaryButton'

const say = sayIn('en')
const NEED = config['clean-days']
const GAP = 12

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

/**
 * The printed Arabic of each ayah a step names, from the Qur'an tab's own
 * endpoint. A step names ayahs of one surah (tests/test_grow.py holds it to that).
 */
function useAyahText(step) {
  const surah = step.ayahs.length ? Number(step.ayahs[0].split(':')[0]) : null
  const found = useQuery({
    ...quranSurahQuery(surah),
    enabled: surah != null,
  })
  const text = useMemo(() => {
    const out = {}
    for (const ayah of found.data?.ayahs ?? []) out[`${surah}:${ayah.ayah}`] = ayah.arabic
    return out
  }, [found.data, surah])
  return { text, loading: found.isLoading, failed: found.isError }
}

/** One honest line under a recitation. Nothing is called right that was not. */
function Verdict({ phase, result }) {
  let text = say('Press the microphone, say it, then press it again.')
  if (phase === 'checking') text = say('Checking each word by sound…')
  if (phase === 'done') {
    const count = tally(result.marks)
    const fix = count[WRONG] + count[MISSED]
    const parts = []
    if (fix) parts.push(say('{n} to fix', { n: fix }))
    if (count[CHECK]) parts.push(say('{n} not sure', { n: count[CHECK] }))
    if (!result.weighed) text = say('The sound could not be checked this time, so this run is shown but not counted.')
    else if (result.clean) text = say('Every word right.')
    else text = `${parts.join(', ')}. ${count[CHECK] && !fix
      ? say('The app could not tell: say it again, slowly and clearly.')
      : say('Look at the marked words and try again.')}`
  }
  return (
    <p className="grow-verdict" data-ok={phase === 'done' && result.clean ? '' : undefined} role="status">{text}</p>
  )
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

/** A posture: what to do, and one Done from the reader, since the ear cannot hear it. */
function Action({ step, record, accent, onGo, onDone, onBloom }) {
  const learnt = isLearnt(record, step.id)
  return (
    <>
      <p className="grow-meaning grow-how">{step.instruction}</p>
      <div className="grow-prac">
        {learnt
          ? <p className="grow-verdict" data-ok="" role="status">{say('Done. This step is learnt.')}</p>
          : <PrimaryButton accent={accent} onClick={() => { onBloom(); onDone() }}>{say('Done')}</PrimaryButton>}
      </div>
      {step.ruling && <Ruling ruling={step.ruling} onGo={onGo} />}
    </>
  )
}

/** The words, the microphone, the marks and the days, for a step that is open. */
function Recital({ step, record, accent, onRecited, onGo, onBloom }) {
  const level = useSetting('reciting-level')
  const ayahText = useAyahText(step)
  const page = useMemo(() => pageOf(step, ayahText.text), [step, ayahText.text])
  // idle, checking (words back, sound being weighed), done
  const [phase, setPhase] = useState('idle')
  const [result, setResult] = useState(null)

  async function heard({ text }, recording) {
    setResult(judge(page.words, text, null, level))
    setPhase('checking')
    const final = judge(page.words, text, await checkStep(step, recording, text, page), level)
    setResult(final)
    setPhase('done')
    // A run whose sound was not weighed is shown, and never counted.
    if (!final.weighed) return
    if (becomesLearnt(record, step.id, final.clean)) onBloom()
    onRecited(final.clean)
  }

  const words = result ? result.marks.words : page.words.map((word) => ({ word, state: WAITING }))

  return (
    <>
      {ayahText.loading && <p className="grow-verdict">{say('Loading the ayahs…')}</p>}
      {ayahText.failed && <ErrorAlert inline title={say('Could not load the ayahs')} />}

      <p
        className="leading-loose text-center"
        dir="rtl"
        data-script={isQuranic(words.map((mark) => mark.word).join(' ')) ? 'quran' : undefined}
      >
        {words.map((mark, i) => (
          <span key={`${i}-${mark.word}`}>
            <ArabicText
              size="lg"
              title={LOOK[mark.state]?.label}
              className={mark.state === MISSED ? 'grow-missed' : undefined}
              style={{ color: LOOK[mark.state]?.colour }}
            >
              {mark.word}
            </ArabicText>{' '}
          </span>
        ))}
      </p>

      {step.meaning && <p className="grow-meaning">{step.meaning}</p>}

      <div className="grow-prac">
        <DaysRing done={Math.min(daysOf(record, step.id), NEED)} />
        <MicButton recite accent={accent} title={say('Say it')} onHeard={heard} />
      </div>
      <Verdict phase={phase} result={result} />

      {step.ruling && <Ruling ruling={step.ruling} onGo={onGo} />}
    </>
  )
}

export default function Practice(props) {
  return byHand(props.step) ? <Action {...props} /> : <Recital {...props} />
}
