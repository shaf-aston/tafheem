/**
 * One Tamreen question at a time: a rule to tick, or a picture's grid to fill
 * in. Checking colours every option (green: right and picked, red dot: wrong
 * and picked, red dotted ring: right and missed) and reveals the teacher's
 * explanation and any doubt. Narrow to one topic, or to only the ones got
 * wrong, and jump to any question from the numbered squares, the way the Quiz
 * tab's strip works. Answers are kept in the browser, so a wrong one is still
 * there to redo tomorrow. Grading and narrowing live in lib/tamreen.
 */
import { KINDS, SHOWS, statusOf } from '../../lib/tamreen'
import { useTamreenPractise } from '../../lib/useTamreenPractise'

import PrimaryButton from '../ui/PrimaryButton'
import SmallButton from '../ui/SmallButton'
import Chip from '../ui/Chip'
import AnswerSquare from '../ui/AnswerSquare'
import AutoAdvanceToggle from '../ui/AutoAdvanceToggle'
import FeedbackButton from '../ui/FeedbackButton'
import Segmented from '../ui/Segmented'
import Disclosure from '../ui/Disclosure'
import EmptyState from '../ui/EmptyState'
import NotesLink from './NotesLink'
import WheelPicker from '../ui/WheelPicker'
import EnterKey from './tamreen/EnterKey'
import ExampleQuestion from './tamreen/ExampleQuestion'
import RuleQuestion from './tamreen/RuleQuestion'

const SHOW_LABEL = { all: 'All', wrong: 'Wrong', todo: 'Not done' }
const KIND_LABEL = { all: 'Both types', rule: 'Rules', example: 'Sentences' }
const KIND_BADGE = { rule: 'Rule · tick all that are true', example: 'Sentence · tarkeeb' }

export default function TamreenPractise({ exercises, tags = [], accent, onProgress, onNotes }) {
  const {
    tag, setTag, show, setShow, kind, setKind, ofKind, topics, counts, list, i, entry, id, saved, checked,
    verdict, done, answers, autoNext, setAutoNext, go, choose, check, toggleRuleOption, toggleGridOption,
    togglePartOption, redo, startOver,
  } = useTamreenPractise({ exercises, tags, onProgress })

  // One row: topic, type, show. Each control names itself, so no separate labels.
  const controls = (
    <div className="flex flex-wrap items-center gap-2">
      <WheelPicker
        label="Topic"
        options={[
          { id: '', label: `Every topic (${ofKind.length})` },
          ...topics.map((t) => ({ id: t.key, label: `${t.en} (${t.size})`, hint: t.ar, keys: [t.ar] })),
        ]}
        value={tag}
        onChange={(key) => choose(() => setTag(key))}
        accent={accent}
        className="min-w-0 w-full sm:w-auto sm:max-w-xs"
      />
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

  const square = (q, n) => {
    const status = statusOf(q, answers)
    return (
      <AnswerSquare
        key={q.item.id}
        status={status}
        number={n + 1}
        current={n === i}
        label={`Question ${n + 1}: ${status || 'not done'}`}
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
            {' · '}{done} answered
          </p>
          {done > 0 && (
            <button type="button" onClick={startOver}
              className="hover:text-[var(--text)] underline underline-offset-2 transition-colors">
              Start over
            </button>
          )}
        </div>
      </div>

      {/* Answered squares plus the one you are on: press one to go back to it.
          Only for a long round, where the full set below starts shut; a short
          one opens it already, and the same squares twice is one too many. */}
      {done > 0 && list.length > 40 && (
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
