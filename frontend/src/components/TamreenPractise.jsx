/**
 * One Tamreen question at a time: a rule to tick, or a picture's grid to fill
 * in. Checking colours every option (green: right and picked, red dot: wrong
 * and picked, red dotted ring: right and missed) and reveals the teacher's
 * explanation and any doubt. Narrow to one topic, or to only the ones got
 * wrong, and jump to any question from the numbered squares, the way the Quiz
 * tab's strip works. Answers are kept in the browser, so a wrong one is still
 * there to redo tomorrow. Grading and narrowing live in lib/tamreen.
 */
import { useEffect, useMemo, useState } from 'react'

import { keyAction, typingElsewhere } from '../lib/answerKeys'
import {
  answerParts, buildQueue, gradeGrid, gradeRule, KINDS, labelOf, narrowQueue, partPicks, rowName, scoreOf, SHOWS, statusOf, TAMREEN,
} from '../lib/tamreen'
import { useAnswers } from '../lib/tamreenAnswers'
import { readViewParam, writeViewParams } from '../lib/tabUrl'
import { useRemembered, useRememberedFlag } from '../lib/useRemembered'

import PrimaryButton from './ui/PrimaryButton'
import SmallButton from './ui/SmallButton'
import Chip from './ui/Chip'
import AnswerSquare from './ui/AnswerSquare'
import AutoAdvanceToggle from './ui/AutoAdvanceToggle'
import FeedbackButton from './ui/FeedbackButton'
import Segmented from './ui/Segmented'
import Disclosure from './ui/Disclosure'
import EmptyState from './ui/EmptyState'
import ArabicText from './ui/ArabicText'
import NotesLink from './NotesLink'
import TamreenAnswerNote from './TamreenAnswerNote'
import TamreenSentence, { TamreenLegend } from './TamreenSentence'

const STATUS_CLASS = {
  ok: 'border-[var(--success)] text-[var(--success)]',
  bad: 'border-[var(--danger)] text-[var(--danger)]',
  miss: 'border-dotted border-2 border-[var(--danger)] text-[var(--danger)]',
  '': 'border-[var(--border)] text-[var(--text)]',
}

// A red dot beside anything wrong or missed, so it never rests on colour alone.
const RedDot = () => <span aria-hidden="true" className="inline-block w-2 h-2 rounded-full bg-[var(--danger)] shrink-0" />

const MARK_LABEL = { ok: 'Right', bad: 'Not true', miss: 'You missed this', '': '' }

// An option as shown: the option, and beside it what it points at in the
// picture when it is only a letter ("A", then the sentence A stands for).
function OptionText({ part, option }) {
  const label = labelOf(part, option)
  return (
    <>
      <span dir="auto">{option}</span>
      {label && <ArabicText size="sm">{label}</ArabicText>}
    </>
  )
}

// A tick-every-true list: a rule question, or one list part of an example.
function OptionList({ part, picked, onToggle, checked }) {
  const graded = checked ? gradeRule(part, picked) : null
  return (
    <div className="space-y-1.5">
      {part.options.map((option, n) => {
        const status = graded ? graded.options.find((o) => o.option === option).status : ''
        const isPicked = picked.has(option)
        return (
          <button
            key={option}
            type="button"
            disabled={checked}
            onClick={() => onToggle(option)}
            aria-pressed={isPicked}
            style={{ '--i': n }}
            className={`rise-in option w-full flex items-center gap-3 px-3 py-2 rounded-[var(--radius-sm)] border text-left
              ${checked ? STATUS_CLASS[status] : isPicked ? 'border-[var(--primary)]' : 'border-[var(--border)]'}`}
          >
            <span
              aria-hidden="true"
              className="w-4 h-4 rounded shrink-0 border border-[var(--border-hi)]"
              style={isPicked ? { background: 'var(--primary)', borderColor: 'var(--primary)' } : undefined}
            />
            <span className="flex-1 flex items-center gap-3 text-left"><OptionText part={part} option={option} /></span>
            {checked && status && (
              <span className="type-small flex items-center gap-1.5">
                {(status === 'bad' || status === 'miss') && <RedDot />}
                {MARK_LABEL[status]}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}

function RuleQuestion({ rule, picked, onToggle, checked }) {
  return (
    <div className="space-y-2">
      <p dir="auto" className="font-medium text-[var(--text)]">{rule.question}</p>
      <OptionList part={rule} picked={picked} onToggle={onToggle} checked={checked} />
    </div>
  )
}

// One grid part: a row per word asked about, a chip per ruling.
function GridPart({ part, picks, onToggle, checked }) {
  const graded = checked ? gradeGrid(part, picks) : null
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <tbody>
          {part.rows.map((row) => {
            const rowGraded = graded?.rows.find((r) => r.row === row)
            return (
              <tr key={row} className="border-t border-[var(--border)]">
                {/* Allowed to wrap: a tarkeeb row names a whole phrase, and held on one line it pushed the choices off a phone. */}
                <th className="text-right font-normal py-2 pr-3 w-1/3 sm:w-auto">
                  <span className="arabic-lg">{rowName(part, row)}</span>
                </th>
                <td className="py-2">
                  <div className="flex flex-wrap gap-1.5">
                    {part.options.map((option) => {
                      const status = rowGraded ? rowGraded.options.find((o) => o.option === option).status : ''
                      const isPicked = (picks[row] ?? []).includes(option)
                      return (
                        <button
                          key={option}
                          type="button"
                          disabled={checked}
                          onClick={() => onToggle(row, option)}
                          aria-pressed={isPicked}
                          aria-label={checked && status ? `${option}: ${MARK_LABEL[status]}` : option}
                          className={`option inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border
                            ${checked ? STATUS_CLASS[status]
                              : isPicked ? 'border-[var(--primary)] text-[var(--primary-hi)]' : 'border-[var(--border)] text-[var(--text-dim)]'}`}
                        >
                          {checked && (status === 'bad' || status === 'miss') && <RedDot />}
                          <OptionText part={part} option={option} />
                        </button>
                      )
                    })}
                  </div>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

// A picture question: its sentence, then every ticked part in the order asked.
function ExampleQuestion({ example, picks, onToggleRow, onToggleOption, checked }) {
  return (
    <div className="space-y-3">
      <TamreenSentence example={example} />
      {example.marked?.length > 0 && <TamreenLegend />}
      {/* Each part rises in after the last. On the part, not its rows: a row
          moving inside the sideways-scroll box flashed a scrollbar. */}
      {answerParts(example).map((part, n) => (
        <div key={part.letter} style={{ '--i': n }} className="rise-in space-y-2">
          {part.question && <p dir="auto" className="type-small text-[var(--text-dim)]">{part.question}</p>}
          {part.rows
            ? <GridPart part={part} picks={partPicks(picks, part)} checked={checked}
                onToggle={(row, option) => onToggleRow(part, row, option)} />
            : <OptionList part={part} picked={new Set(partPicks(picks, part))} checked={checked}
                onToggle={(option) => onToggleOption(part, option)} />}
        </div>
      ))}
      {checked && <TamreenAnswerNote example={example} />}
    </div>
  )
}

const SHOW_LABEL = { all: 'All', wrong: 'Wrong', todo: 'Not done' }
const KIND_LABEL = { all: 'Both types', rule: 'Rules', example: 'Sentences' }
const KIND_BADGE = { rule: 'Rule · tick all that are true', example: 'Sentence · tarkeeb' }
// The key printed on the button it fires, so the shortcut is learnt where it is
// used rather than from a line of hints.
const EnterKey = () => (
  <kbd aria-hidden="true"
    className="px-1.5 py-0.5 rounded type-tiny font-semibold leading-none bg-[var(--bg)]/25 border border-current/30">
    Enter ↵
  </kbd>
)


export default function TamreenPractise({ exercises, tags = [], accent, onProgress, onNotes }) {
  const queue = useMemo(() => buildQueue(exercises), [exercises])
  const [answers, setAnswers] = useAnswers()
  const [autoNext, setAutoNext] = useRememberedFlag('tamreen-auto-next', TAMREEN.autoNext)
  // The question just checked: the only one allowed to move on by itself, so
  // looking back over an answered question never walks away from you.
  const [checkedId, setCheckedId] = useState(null)
  // Each choice opens from the address first, then from last visit, and is written back to the address.
  const [savedTag, rememberTag] = useRemembered('tamreen-topic')
  const [savedShow, rememberShow] = useRemembered('tamreen-show', SHOWS)
  const [savedKind, rememberKind] = useRemembered('tamreen-kind', KINDS)
  const [tag, setTagNow] = useState(() => readViewParam('topic') ?? savedTag)
  const [show, setShowNow] = useState(() => readViewParam('show', SHOWS) ?? savedShow)
  const [kind, setKindNow] = useState(() => readViewParam('kind', KINDS) ?? savedKind)
  const setTag = (v) => { setTagNow(v); rememberTag(v) }
  const setShow = (v) => { setShowNow(v); rememberShow(v) }
  const setKind = (v) => { setKindNow(v); rememberKind(v) }
  // The question on screen, by id, so narrowing or checking never swaps it underneath you.
  const [currentId, setCurrentId] = useState(() => readViewParam('question'))

  // Topics that have at least one question of this type, busiest first, each with its count.
  const ofKind = useMemo(() => narrowQueue(queue, {}, { kind }), [queue, kind])
  const topics = useMemo(() => tags
    .map((t) => ({ ...t, size: ofKind.filter((e) => e.item.tags?.includes(t.key)).length }))
    .filter((t) => t.size > 0)
    .sort((a, b) => b.size - a.size), [tags, ofKind])

  const inTopic = narrowQueue(queue, answers, { tag, kind })
  const counts = { all: inTopic.length, ...scoreOf(inTopic, answers) }
  counts.todo = counts.all - counts.right - counts.wrong
  // The current question stays listed while you look at it, even once it no longer fits the view.
  const list = inTopic.filter((e) => e.item.id === currentId || narrowQueue([e], answers, { show }).length)
  // With nothing chosen, open on the first question not yet done rather than question 1 again.
  const firstTodo = list.findIndex((e) => statusOf(e, answers) === '')
  const at = list.findIndex((e) => e.item.id === currentId)
  const i = at >= 0 ? at : Math.max(0, firstTodo)
  const entry = list[i]
  const shownId = entry?.item.id ?? ''
  useEffect(() => {
    writeViewParams({ topic: tag, kind: kind === 'all' ? '' : kind, show: show === 'all' ? '' : show, question: shownId })
  }, [tag, kind, show, shownId])

  // Moving away ends the freshly-checked question: come back to it later and it
  // sits still instead of walking on again under the auto-advance wait.
  const go = (n) => { setCheckedId(null); setCurrentId(list[n]?.item.id ?? null) }
  const choose = (next) => { setCheckedId(null); setCurrentId(null); next() }

  const id = entry?.item.id ?? ''
  const saved = answers[id] ?? {}
  const checked = !!saved.checked
  const save = (patch) => setAnswers((prev) => ({ ...prev, [id]: { ...prev[id], ...patch } }))
  // Pinned as well as checked: with nothing chosen the panel opens on the first
  // question not yet done, so without this a check would slide to the next
  // question before the marks could be read.
  const check = () => { setCurrentId(id); setCheckedId(id); save({ checked: true }) }
  const flip = (list, option) => (list.includes(option) ? list.filter((o) => o !== option) : [...list, option])
  const toggleRuleOption = (option) => {
    const current = saved.picks ?? []
    save({ picks: flip(current, option) })
  }
  // An example's picks are kept per part letter, a grid's by row inside that.
  // Rebuilt from the parts on every save, which also moves an old save (rows
  // at the top) under its grid's letter.
  const savePart = (part, own) => save({
    picks: { ...Object.fromEntries(answerParts(entry.item).map((p) => [p.letter, partPicks(saved.picks, p)])), [part.letter]: own },
  })
  const toggleGridOption = (part, row, option) => {
    const own = partPicks(saved.picks, part)
    savePart(part, { ...own, [row]: flip(own[row] ?? [], option) })
  }
  const togglePartOption = (part, option) => savePart(part, flip(partPicks(saved.picks, part), option))
  const verdict = checked && entry ? statusOf(entry, answers) : ''

  // Answer without reaching for the mouse, the Quiz's keys and the Quiz's
  // guards: a digit ticks an option, Enter checks and then moves on, A flips
  // auto-advance. No dependency list, on purpose: the handler reads what is on
  // screen now, so it is replaced on every render, like the Quiz's.
  useEffect(() => {
    const onKeyDown = (e) => {
      if (typingElsewhere(e) || !entry) return
      const options = entry.kind === 'rule' ? entry.item.options : []
      const action = keyAction(e.key, { checked, optionCount: options.length })
      if (!action) return
      // Immediate, not plain stopPropagation: the app's 1-5 tab shortcut listens
      // on window too, so a digit would both tick an option and change tab.
      if (action.do !== 'check' && action.do !== 'next') e.stopImmediatePropagation()
      if (action.do === 'auto') setAutoNext(!autoNext)
      if (action.do === 'toggle') toggleRuleOption(options[action.index])
      if (action.do === 'check') check()
      if (action.do === 'next' && i < list.length - 1) go(i + 1)
    }
    window.addEventListener('keydown', onKeyDown, true)
    return () => window.removeEventListener('keydown', onKeyDown, true)
  })

  // The pause that makes the marks readable: a right answer only needs a
  // glance, a wrong one has to be read before it goes.
  // Fixed dependencies, so an unrelated re-render never restarts the wait.
  const nextId = list[i + 1]?.item.id
  useEffect(() => {
    if (!autoNext || !verdict || checkedId !== id || !nextId) return
    const timer = setTimeout(() => { setCheckedId(null); setCurrentId(nextId) },
      verdict === 'right' ? TAMREEN.autoNextMs : TAMREEN.autoNextWrongMs)
    return () => clearTimeout(timer)
  }, [autoNext, verdict, checkedId, id, nextId])

  // The header pen cheers or droops for the question just checked, as it does
  // for the Quiz; looking back at an old answer says nothing.
  const fresh = checkedId === id ? verdict : ''
  useEffect(() => {
    onProgress?.({ streak: 0, answer: fresh === 'right' ? 'correct' : fresh === 'wrong' ? 'wrong' : null })
    // Leaving Practise (Browse, another Nahw view) puts the pen back to rest.
    return () => onProgress?.({ streak: 0, answer: null })
  }, [onProgress, fresh])

  // One row: topic, type, show. Each control names itself, so no separate labels.
  const controls = (
    <div className="flex flex-wrap items-center gap-2">
      <select
        aria-label="Topic"
        value={tag}
        onChange={(e) => choose(() => setTag(e.target.value))}
        style={{ '--c': accent }}
        className="py-1.5 px-3 rounded-full text-sm min-w-0 w-full sm:w-auto sm:max-w-xs bg-[var(--surface)] border
          border-[var(--border-hi)] text-[var(--text)] focus:border-[var(--c)] focus:outline-none transition-colors"
      >
        <option value="">Every topic ({ofKind.length})</option>
        {topics.map((t) => <option key={t.key} value={t.key}>{t.en} · {t.ar} ({t.size})</option>)}
      </select>
      <Segmented label="Question type" options={KINDS.map((id) => ({ id, label: KIND_LABEL[id] }))}
        value={kind} accent={accent} onChange={(id) => choose(() => setKind(id))} />
      <Segmented
        label="Show"
        options={SHOWS.map((id) => ({ id, label: `${SHOW_LABEL[id]} · ${counts[id]}` }))}
        value={show}
        accent={accent}
        onChange={(id) => choose(() => setShow(id))}
      />
    </div>
  )

  if (!entry) {
    return (
      <div className="space-y-4">
        {controls}
        <EmptyState>
          {show === 'wrong' ? 'Nothing wrong here to redo. Questions you get wrong collect here.'
            : show === 'todo' ? 'Every question here is done. Pick All to look back over them.'
              : 'No questions on this topic yet.'}
        </EmptyState>
      </div>
    )
  }

  const redo = () => {
    setAnswers((prev) => { const next = { ...prev }; delete next[id]; return next })
    setCurrentId(id)
  }
  const startOver = () => setAnswers((prev) => {
    const next = { ...prev }
    for (const e of inTopic) delete next[e.item.id]
    return next
  })
  const done = counts.right + counts.wrong
  const square = (q, n) => {
    const status = statusOf(q, answers)
    return (
      <AnswerSquare
        key={q.item.id}
        status={status}
        number={n + 1}
        current={n === i}
        label={`Question ${n + 1}: ${status || 'not done'}`}
        accent={accent}
        onClick={() => go(n)}
      />
    )
  }

  return (
    <div className="space-y-4" style={{ '--c': accent }}>
      {controls}

      {/* Where you are, what kind of question, and its topics (press one to practise only that). */}
      <div className="flex flex-wrap items-center gap-2">
        <p className="text-sm font-medium text-[var(--text)] me-1">Question {i + 1} of {list.length}</p>
        <span className="type-small text-[var(--text-faint)] me-auto">{KIND_BADGE[entry.kind]}</span>
        {entry.item.tags.map((key) => {
          const named = tags.find((one) => one.key === key)
          return (
            <Chip key={key} accent={accent} arabic={!!named} selected={key === tag}
              title={named ? `${named.en}: practise only this topic` : key}
              onClick={() => choose(() => setTag(key))}>
              {named?.ar ?? key}
            </Chip>
          )
        })}
        <NotesLink exerciseKey={entry.exerciseKey} accent={accent} onOpen={onNotes} />
      </div>

      <div key={id} className="rise-in">
        {entry.kind === 'rule'
          ? <RuleQuestion rule={entry.item} picked={new Set(saved.picks ?? [])} onToggle={toggleRuleOption} checked={checked} />
          : <ExampleQuestion example={entry.item} picks={saved.picks ?? {}} checked={checked}
              onToggleRow={toggleGridOption} onToggleOption={togglePartOption} />}
      </div>

      <div className="flex items-center justify-between gap-3">
        <SmallButton disabled={i === 0} onClick={() => go(i - 1)}>Back</SmallButton>
        {/* Said in words, not only in colour, and the reason for the pause. */}
        <p aria-live="polite" className="type-small font-medium me-auto"
          style={{ color: verdict === 'right' ? 'var(--success)' : 'var(--danger)' }}>
          {verdict && <span key={id} className="fade-in">{verdict === 'right' ? 'Right' : 'Not quite'}</span>}
        </p>
        <div className="flex items-center gap-3">
          {checked && <SmallButton onClick={redo}>Redo</SmallButton>}
          {!checked && i < list.length - 1 && (
            <SmallButton onClick={() => go(i + 1)}>Skip</SmallButton>
          )}
          <div className={checked ? 'w-48' : 'w-36'}>
            {checked ? (
              <PrimaryButton accent={accent} disabled={i >= list.length - 1} onClick={() => go(i + 1)}>
                Next question<EnterKey />
              </PrimaryButton>
            ) : (
              <PrimaryButton accent={accent} onClick={check}>Check<EnterKey /></PrimaryButton>
            )}
          </div>
        </div>
      </div>

      {/* Centred under the row it governs, where the Quiz puts it. */}
      <div className="flex justify-center">
        <AutoAdvanceToggle value={autoNext} onChange={setAutoNext} accent={accent} />
      </div>

      {/* Bottom, in the Quiz tab's order: progress bar, score line, then the answered squares. */}
      <div className="space-y-1.5">
        <div className="h-1 rounded-full bg-[var(--surface)] overflow-hidden" aria-hidden="true">
          <div
            className="h-full rounded-full transition-[width] duration-[calc(var(--motion-spring-ms)*1ms)]"
            style={{ width: `${counts.all ? (done / counts.all) * 100 : 0}%`, background: accent }}
          />
        </div>
        <div className="flex items-center justify-between gap-4 type-small text-[var(--text-faint)] flex-wrap">
          <p>
            <span className="text-[var(--text)] font-medium tabular-nums">{counts.right}/{done}</span>
            {done > 0 && <> · {Math.round((counts.right / done) * 100)}%</>}
            {' · '}{done} of {counts.all} answered
          </p>
          {done > 0 && (
            <button type="button" onClick={startOver}
              className="hover:text-[var(--text)] underline underline-offset-2 transition-colors">
              Start over
            </button>
          )}
        </div>
      </div>

      {/* Answered squares plus the one you are on: press one to go back to it. */}
      {done > 0 && (
        <div className="flex flex-wrap items-start justify-center gap-1.5" role="group" aria-label="Answered questions">
          {list.map((q, n) => (statusOf(q, answers) || n === i ? square(q, n) : null))}
        </div>
      )}

      <div className="flex items-start justify-between gap-3 flex-wrap">
        <Disclosure label={`All ${list.length} questions`} defaultOpen={list.length <= 40} className="flex-1">
          <div className="pt-2 flex flex-wrap gap-1.5" role="group" aria-label="Questions">
            {list.map(square)}
          </div>
        </Disclosure>
        <FeedbackButton module="tamreen" item={id} accent={accent} />
      </div>
    </div>
  )
}
