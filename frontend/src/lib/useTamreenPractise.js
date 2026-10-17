import { useEffect, useMemo, useState } from 'react'

import { useAnswerKeys } from './useAnswerKeys'
import { answerParts, buildQueue, KINDS, narrowQueue, partPicks, scoreOf, SHOWS, statusOf, TAMREEN } from './tamreen'
import { useAnswers } from './tamreenAnswers'
import { readViewParam, writeViewParams } from './tabUrl'
import { useRemembered, useRememberedFlag } from './useRemembered'

/**
 * Everything the Tamreen practise panel holds: which topic, type and show are
 * chosen, the question on screen and where it sits in the list, the saved
 * picks and checks, and what ticking, checking and moving do to them. Also
 * the answer keys, the auto-advance wait and the header pen.
 */
export function useTamreenPractise({ exercises, tags, onProgress }) {
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
  // auto-advance.
  const keyOptions = entry?.kind === 'rule' ? entry.item.options : []
  useAnswerKeys(entry && { checked, optionCount: keyOptions.length }, {
    auto: () => setAutoNext(!autoNext),
    toggle: (e, index) => toggleRuleOption(keyOptions[index]),
    check: () => check(),
    next: () => { if (i < list.length - 1) go(i + 1) },
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

  return {
    tag, setTag, show, setShow, kind, setKind, ofKind, topics, counts, list, i, entry, id, saved, checked,
    verdict, done, answers, autoNext, setAutoNext, go, choose, check, toggleRuleOption, toggleGridOption,
    togglePartOption, redo, startOver,
  }
}
