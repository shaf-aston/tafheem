/**
 * What a key press means while a question is on screen. Shared by the Quiz and
 * by Tamreen Practise, so "a digit answers, Enter is the way on, A flips
 * auto-advance" is written down once and both tabs answer the same way.
 *
 * Pure: a key and the state of the question in, an action out. Which button
 * that action presses is the panel's business.
 */

/**
 * `{ do: 'auto' | 'check' | 'next' | 'toggle' | 'swallow', index? }`, or null
 * for a key that is none of ours.
 *
 * 'swallow' is a digit that names an option on screen but cannot act on it,
 * because the answer is already showing. It still belongs to this question and
 * must not reach the app's own 1-5 tab shortcuts and leave mid-answer. A digit
 * naming no option, on a question with none or past the last one, is not ours:
 * it falls through and changes tab.
 *
 * A panel that answers in one press (the Quiz) reads 'toggle' as its pick and
 * ignores 'check'; a panel that ticks several and then checks (Tamreen) uses
 * both.
 */
export function keyAction(key, { checked = false, optionCount = 0 } = {}) {
  if (key === 'a' || key === 'A') return { do: 'auto' }
  if (key === 'Enter') return { do: checked ? 'next' : 'check' }
  const index = Number.parseInt(key, 10) - 1
  if (!(index >= 0 && index < optionCount)) return null
  return checked ? { do: 'swallow' } : { do: 'toggle', index }
}

/**
 * True while the key belongs to the page rather than to this question: typing
 * in a search box, or a shortcut held with a modifier.
 */
export function typingElsewhere(e, el = document.activeElement) {
  if (el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.isContentEditable)) return true
  return !!(e.metaKey || e.ctrlKey || e.altKey)
}
