/**
 * Save a Qur'an word for Review, from its card in the reader. A toggle, so a
 * word saved by mistake is one more press; the line beside it says once where
 * a saved word goes, aloud as well (role="status"), because "Saved" alone
 * leaves the reader asking: saved where? Nothing for a word Review cannot ask
 * (lib/quiz/useSavedWord.js).
 */
import { useState } from 'react'

import { useSavedWord } from '../../lib/quiz/useSavedWord'

export default function SaveWord({ word }) {
  const { canSave, saved, toggle } = useSavedWord(word)
  // Said only after a press here, not on opening a word saved long ago.
  const [said, setSaid] = useState('')
  if (!canSave) return null

  const press = () => {
    toggle()
    setSaid(saved ? 'No longer saved' : 'Saved → comes back in Review')
  }

  return (
    <span className="save-word">
      <button
        type="button"
        aria-pressed={saved}
        onClick={press}
        title={saved ? 'Saved for Review: press to remove' : 'Save this word for Review'}
        className="save-word-toggle tap type-small"
      >
        <svg aria-hidden="true" viewBox="0 0 24 24" fill={saved ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" strokeLinejoin="round">
          <path d="M6 3h12v18l-6-4.5L6 21z" />
        </svg>
        {saved ? 'Saved' : 'Save'}
      </button>
      <span role="status" className="save-word-said type-small">{said}</span>
    </span>
  )
}
