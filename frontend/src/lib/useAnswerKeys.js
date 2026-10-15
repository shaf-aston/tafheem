/**
 * The Quiz's and Tamreen's keyboard, wired once: keyAction says what a key
 * means, this listens for it and calls the panel's handler of that name
 * (`auto`, `speak`, `toggle`, `check`, `next`), each given the event and the
 * option's index. `question` is `{ checked, optionCount }`, or null while
 * nothing is on screen to answer.
 *
 * No dependency list, on purpose: the handlers read what is on screen now, so
 * the listener is replaced on every render.
 */
import { useEffect } from 'react'

import { keyAction, typingElsewhere } from './answerKeys'

export function useAnswerKeys(question, handlers) {
  useEffect(() => {
    const onKeyDown = (e) => {
      if (typingElsewhere(e) || !question) return
      const action = keyAction(e.key, question)
      if (!action) return
      // Immediate, not plain stopPropagation: the app's tab shortcut listens on
      // window too, and plain stopPropagation does not stop a second listener on
      // the same target, so 2 would answer the question AND open Quran, and a 2
      // pressed with an answer already on screen would leave the panel outright.
      if (action.do !== 'check' && action.do !== 'next') e.stopImmediatePropagation()
      handlers[action.do]?.(e, action.index)
    }
    window.addEventListener('keydown', onKeyDown, true)
    return () => window.removeEventListener('keydown', onKeyDown, true)
  })
}
