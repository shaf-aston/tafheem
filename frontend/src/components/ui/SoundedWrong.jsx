/**
 * One tap to say the voice got a word wrong. Files what was last heard (the
 * text, which voice, what speed) through the same feedback box as "Report a
 * problem" (lib/progress.js), under module "voice", so the words to fix are
 * the ones people actually heard wrong, not guesses. Shown once a word has
 * been heard, keyed on the question by its caller so it resets with it.
 */
import { useState } from 'react'

import { leaveFeedback } from '../../lib/progress'
import { lastHeard } from '../../lib/speak'

export default function SoundedWrong({ className = '' }) {
  const [state, setState] = useState('') // '' | 'unheard' | 'sending' | 'sent' | 'failed'
  const send = async () => {
    const heard = lastHeard()
    if (!heard) return setState('unheard')
    setState('sending')
    const { saved } = await leaveFeedback({
      module: 'voice',
      item: heard.text.slice(0, 200),
      message: `sounded wrong (${heard.voice}, ${heard.speed}${heard.accent ? `, ${heard.accent}` : ''})`,
    })
    setState(saved ? 'sent' : 'failed')
  }
  return (
    <button
      type="button"
      onClick={send}
      disabled={state === 'sending' || state === 'sent'}
      className={`type-small text-[var(--text-faint)] hover:text-[var(--text)] transition-colors disabled:cursor-default ${className}`}
    >
      {{ sent: 'Thanks, noted', failed: 'Couldn’t send, tap again', unheard: 'Play it first' }[state] ?? 'Sounded wrong?'}
    </button>
  )
}
