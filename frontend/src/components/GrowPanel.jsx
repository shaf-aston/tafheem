/**
 * Grow, نَبَات: a straight path through what a person says in their prayer,
 * one step at a time, and an honest answer to "did I say it right?".
 *
 *   وَأَنبَتَهَا نَبَاتًا حَسَنًا (3:37), and He made her grow a good growth.
 *
 * Three promises decide everything on this page:
 *   1. No ruling is the app's own. The ear judges how a word was said, never
 *      what the prayer requires; what the prayer requires is quoted from a
 *      named scholar's book, word for word, and kept out of the way until
 *      asked for (tests/test_grow.py holds every quote to the book).
 *   2. "Not sure" is said when it is not sure, and it never counts as right.
 *   3. The score is what has been mastered, not what has been opened.
 *
 * Its own module: the paths come from /api/grow/paths, the marking and the
 * record are lib/grow.js, and everything else it uses is the app's shared
 * pieces, the same microphone, the same word colours, the same ear checks,
 * so nothing here changes how any other tab behaves.
 */
import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { checkReading, checkText, getGrowPaths, getQuranSurah } from '../api'
import { CHECK, MISSED, SAID, WRONG } from '../lib/follow'
import {
  afterRecitation, isClean, isMastered, loadRecord, markRecitation, nextStep, pageOf, saveRecord, score, tally,
} from '../lib/grow'
import config from '../grow.json'
import { recordAttempt } from '../lib/progress'
import { LOOK } from '../lib/reciteColors'
import { byPlace } from '../lib/recitingSession'
import { useRemembered } from '../lib/useRemembered'
import { useSetting } from '../lib/settings'
import ArabicText from './ui/ArabicText'
import Disclosure from './ui/Disclosure'
import ErrorAlert from './ui/ErrorAlert'
import MicButton from './ui/MicButton'
import SectionHeader from './ui/SectionHeader'
import Segmented from './ui/Segmented'

const PATHS = ['salah', 'surahs']

export default function GrowPanel({ accent, onGo }) {
  const paths = useQuery({ queryKey: ['grow-paths'], queryFn: getGrowPaths, staleTime: Infinity })
  const [pathId, setPathId] = useRemembered('grow-path', PATHS)
  const [record, setRecord] = useState(loadRecord)
  const path = paths.data?.find((one) => one.id === pathId) ?? paths.data?.[0] ?? null
  const [stepId, setStepId] = useState(null)
  const step = path?.steps.find((one) => one.id === stepId) ?? nextStep(path, record)

  useEffect(() => { saveRecord(record) }, [record])

  const done = score(path, record)

  return (
    <div className="space-y-5">
      <SectionHeader
        title="Grow!"
        arabic="نَبَات"
        subtitle="Learn to say it right, one step at a time. The app listens and marks each word; the rulings are the scholars'."
      />

      {paths.isError && <ErrorAlert title="Could not load the paths">Check the connection and try again.</ErrorAlert>}

      {path && (
        <>
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <Segmented
              label="Path"
              accent={accent}
              value={path.id}
              onChange={(id) => { setPathId(id); setStepId(null) }}
              options={paths.data.map((one) => ({ id: one.id, label: one.title }))}
            />
            <p className="type-small text-[var(--text-dim)] tabular-nums" title="Only steps said right on two different days count">
              {done.mastered} of {done.total} mastered
            </p>
          </div>

          <ol className="flex flex-wrap gap-1.5" aria-label="Steps">
            {path.steps.map((one, i) => {
              const on = one.id === step?.id
              const mastered = isMastered(record, one.id)
              return (
                <li key={one.id}>
                  <button
                    type="button"
                    onClick={() => setStepId(one.id)}
                    aria-current={on ? 'step' : undefined}
                    className={`press px-2.5 py-1 rounded-full border text-xs transition-colors ${
                      on ? 'text-[var(--text)]' : 'text-[var(--text-faint)] hover:text-[var(--text-dim)]'}`}
                    style={on
                      ? { borderColor: accent, background: `color-mix(in srgb, ${accent} 14%, transparent)` }
                      : { borderColor: 'var(--border)' }}
                  >
                    <span className="tabular-nums">{i + 1}.</span> {one.title}
                    {mastered && <span aria-label="mastered" style={{ color: accent }}> ✓</span>}
                  </button>
                </li>
              )
            })}
          </ol>

          {step && (
            <Step
              key={`${path.id}/${step.id}`}
              step={step}
              accent={accent}
              entry={record[step.id]}
              onGo={onGo}
              onRecited={(clean) => {
                setRecord((was) => afterRecitation(was, step.id, clean))
                recordAttempt({ module: 'grow', item: `${path.id}/${step.id}`, correct: clean, context: { path: path.id } })
              }}
            />
          )}
        </>
      )}
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

/** One step: the words, the microphone, the marks, and the scholar's words on it. */
function Step({ step, accent, entry, onGo, onRecited }) {
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
      if (step.ayahs?.length) {
        const answer = await checkReading(recording, { heard: text, check: step.ayahs })
        sure = byPlace(answer.sure, page.ayahs)
      } else {
        sure = (await checkText(recording, { heard: text, expected: step.arabic })).sure
      }
    } catch {
      sure = null
    }
    // Clean only when the sound was actually weighed for every word. A run the
    // ear could not check is shown, and never counted.
    const weighed = sure != null && page.words.every((_, i) => sure[i] != null)
    const final = markRecitation(page.words, text, sure ?? [], level)
    setMarks(final)
    setPhase('done')
    if (!weighed) setNote('The sound could not be checked this time, so this run is shown but not counted.')
    onRecited(weighed && isClean(final))
  }

  const cleanDays = entry?.cleanDays?.length ?? 0
  const words = marks?.words ?? page.words.map((word) => ({ word, state: 'waiting' }))

  return (
    <section
      className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4 space-y-4"
      aria-label={step.title}
    >
      <div className="flex items-baseline justify-between gap-3 flex-wrap">
        <h3 className="text-base font-semibold text-[var(--text)]">{step.title}</h3>
        <p className="type-tiny text-[var(--text-faint)] tabular-nums">
          {cleanDays >= config['clean-days']
            ? 'Mastered'
            : `Said right on ${cleanDays} of ${config['clean-days']} days`}
        </p>
      </div>

      {ayahText.loading && <p className="type-small text-[var(--text-faint)]">Loading the ayahs…</p>}
      {ayahText.failed && <ErrorAlert inline title="Could not load the ayahs" />}

      <p className="leading-loose" dir="rtl">
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

      {step.meaning && <p className="type-small text-[var(--text-dim)] max-w-prose">{step.meaning}</p>}

      <div className="flex items-center gap-3 flex-wrap">
        <MicButton recite accent={accent} title="Say it" onHeard={heard} />
        <Verdict phase={phase} marks={marks} note={note} />
      </div>

      {step.ruling && <Ruling ruling={step.ruling} onGo={onGo} />}
    </section>
  )
}

/** One honest line under a recitation. Nothing is called right that was not. */
function Verdict({ phase, marks, note }) {
  if (phase === 'idle') return <p className="type-small text-[var(--text-faint)]">Press the microphone, say it, then press it again.</p>
  if (phase === 'checking') return <p className="type-small text-[var(--text-faint)]">Checking each word by sound…</p>
  const count = tally(marks)
  const parts = []
  if (count[WRONG] + count[MISSED]) parts.push(`${count[WRONG] + count[MISSED]} to fix`)
  if (count[CHECK]) parts.push(`${count[CHECK]} not sure`)
  const text = note || (isClean(marks)
    ? 'Every word right.'
    : `${parts.join(', ')}. ${count[CHECK] && !(count[WRONG] + count[MISSED])
      ? 'The app could not tell: say it again, slowly and clearly.'
      : 'Look at the marked words and try again.'}`)
  return (
    <p className="type-small" style={{ color: isClean(marks) && !note ? LOOK[SAID].colour : 'var(--text-dim)' }} role="status">
      {text}
    </p>
  )
}

/**
 * The scholar's words on this step, shut until asked for. The book and the
 * chapter are one faint line under the quote: there for anyone who wants to
 * find it, not in the way of anyone who does not.
 */
function Ruling({ ruling, onGo }) {
  return (
    // "Abu al-Husayn al-Quduri (d. 428 AH)" is named by the name he is known by.
    <Disclosure label={`What ${ruling.author.split(' (')[0].split(' ').pop()} says`}>
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
                onClick={() => onGo('daleel', ruling.arabic.split(' ').slice(0, 8).join(' '))}
                className="underline underline-offset-2 hover:text-[var(--text-dim)]"
              >
                Open in Daleel
              </button>
            </>
          )}
        </p>
      </div>
    </Disclosure>
  )
}
