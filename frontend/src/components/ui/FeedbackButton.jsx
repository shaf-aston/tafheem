/**
 * A quiet "Report a problem" pill for any panel. Opens a small box to say what
 * looks wrong; the note is filed with the module and the question it is about.
 * Resets when the question changes, so a note never lands on the wrong one.
 */
import { useState } from 'react'
import { leaveFeedback } from '../../lib/progress'
import Popover from './Popover'
import PrimaryButton from './PrimaryButton'

// Keyed on the question: a new question starts a fresh, closed box.
export default function FeedbackButton(props) {
  return <Feedback key={props.item ?? ''} {...props} />
}

function Feedback({ module, item, accent }) {
  const [message, setMessage] = useState('')
  const [state, setState] = useState('') // '' | 'sending' | 'sent' | 'failed'

  const send = async (event) => {
    event.preventDefault()
    if (!message.trim()) return
    setState('sending')
    const { saved } = await leaveFeedback({ module, item, message: message.trim() })
    setState(saved ? 'sent' : 'failed')
    if (saved) setMessage('')
  }

  return (
    <Popover label="Report a problem" title="Something wrong with this question?">
      {state === 'sent' ? (
        <p role="status" className="type-small text-[var(--text)] w-64">Thanks, sent.</p>
      ) : (
        <form onSubmit={send} className="w-64 space-y-2">
          <label htmlFor={`feedback-${module}`} className="block type-small text-[var(--text-dim)]">
            What looks wrong?
          </label>
          <textarea
            id={`feedback-${module}`}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            maxLength={2000}
            rows={3}
            placeholder="e.g. the answer marked right is wrong"
            className="w-full p-2 rounded-[var(--radius-sm)] type-small bg-[var(--surface)] border
              border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-[var(--border-hi)]"
          />
          {state === 'failed' && (
            <p role="alert" className="type-small text-[var(--danger)]">Couldn’t send. Try again in a moment.</p>
          )}
          <PrimaryButton accent={accent} type="submit" disabled={!message.trim()} loading={state === 'sending'}>
            Send
          </PrimaryButton>
        </form>
      )}
    </Popover>
  )
}
