/**
 * The site's one line for the person reading it: a note (a mistake, an idea) and,
 * if they want, an email for a reply or for the occasional update. Shown at the
 * foot of the app and of the landing page, filed with the panels' "Report a
 * problem" notes (module "site", item = where it was written).
 *
 * One line until it is used. The email and the updates box open when the note
 * is being written, or straight away from "Get updates", which is the whole of
 * the mailing list: an email and a ticked box, no message needed.
 */
import { useId, useRef, useState } from 'react'
import { leaveFeedback } from '../../lib/learner/progress'

// Loose on purpose: the server checks the same shape, and a typo the reader sees beats a refusal they don't.
const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/

export default function FooterNote({ where, accent = 'var(--primary)' }) {
  const id = useId()
  const emailRef = useRef(null)
  const [message, setMessage] = useState('')
  const [email, setEmail] = useState('')
  const [updates, setUpdates] = useState(false)
  const [open, setOpen] = useState(false)
  const [state, setState] = useState('') // '' | 'sending' | 'sent' | 'failed'
  const [sent, setSent] = useState(null) // what went, for the thank-you line

  const said = message.trim()
  const address = email.trim()
  const emailOk = EMAIL.test(address)
  const emailWrong = address !== '' && !emailOk
  // Something to act on, and nothing half-typed: a note, or a request for updates with an address to send them to.
  const ready = (said !== '' || updates) && (address === '' ? !updates : emailOk)

  const getUpdates = () => {
    setOpen(true)
    setUpdates(true)
    // After the row renders, so the field exists to take the cursor.
    requestAnimationFrame(() => emailRef.current?.focus())
  }

  const send = async (event) => {
    event.preventDefault()
    if (!ready || state === 'sending') return
    setState('sending')
    const { saved } = await leaveFeedback({
      module: 'site', item: where, message: said, email: address || undefined, updates,
    })
    if (!saved) return setState('failed')
    setSent({ note: said !== '', email: address, updates })
    setMessage(''); setEmail(''); setUpdates(false); setOpen(false)
    setState('sent')
  }

  if (state === 'sent') {
    return (
      <div className="footer-note" style={{ '--c': accent }}>
        <p role="status" className="footer-note-row">
          <span>{thanks(sent)}</span>
          <button type="button" className="footer-note-link" onClick={() => setState('')}>Write another</button>
        </p>
      </div>
    )
  }

  return (
    <form className="footer-note" style={{ '--c': accent }} onSubmit={send} noValidate>
      <div className="footer-note-row">
        <label htmlFor={`${id}-message`}>Spotted a mistake or have an idea?</label>
        <span className="footer-note-field">
          <input
            id={`${id}-message`}
            type="text"
            value={message}
            onChange={(e) => { setMessage(e.target.value); if (e.target.value) setOpen(true) }}
            onFocus={() => setOpen(true)}
            maxLength={2000}
            enterKeyHint="send"
            placeholder="Write it here"
          />
          <button type="submit" className="footer-note-send" disabled={!ready} aria-busy={state === 'sending'}>
            {state === 'sending' ? 'Sending' : 'Send'}
          </button>
        </span>
        {!open && <button type="button" className="footer-note-link" onClick={getUpdates}>Get updates by email</button>}
      </div>

      {open && (
        <div className="footer-note-row footer-note-more">
          <label htmlFor={`${id}-email`}>Email, if you’d like a reply</label>
          <input
            ref={emailRef}
            id={`${id}-email`}
            type="email"
            inputMode="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            maxLength={254}
            placeholder="you@example.com"
            aria-invalid={emailWrong || undefined}
            aria-describedby={emailWrong ? `${id}-email-error` : undefined}
          />
          <label className="footer-note-check">
            <input type="checkbox" checked={updates} onChange={(e) => setUpdates(e.target.checked)} />
            Send me the occasional update
          </label>
        </div>
      )}

      {emailWrong && (
        <p id={`${id}-email-error`} role="alert" className="footer-note-error">
          That email is missing an @ or a domain, like name@example.com.
        </p>
      )}
      {updates && address === '' && open && (
        <p className="footer-note-hint">Add your email above and updates will go there.</p>
      )}
      {state === 'failed' && (
        <p role="alert" className="footer-note-error">
          Couldn’t send just now. Your note is still here, so try Send again in a moment.
        </p>
      )}
    </form>
  )
}

/** The thank-you line: says what happened to what they sent, in their own terms. */
function thanks({ note, email, updates }) {
  if (!note) return `Thanks. Updates will go to ${email}.`
  if (updates) return `Thanks, your note is in. Updates will go to ${email}.`
  if (email) return `Thanks, your note is in. Any reply will go to ${email}.`
  return 'Thanks, your note is in.'
}
