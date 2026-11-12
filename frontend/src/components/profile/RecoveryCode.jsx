/**
 * An account's recovery code, shown the one time it exists in the clear: the server keeps only a seal of it
 * (backend/services/learner/tokens.py). It is how this account logs in on another device, so the panel says
 * that plainly and offers a copy. `onDone`, when given, is the "I've saved it" step that carries on (sign-up
 * waits on it); without it the code just sits there until the profile closes.
 */
import CopyButton from '../ui/buttons/CopyButton'
import PrimaryButton from '../ui/buttons/PrimaryButton'

export default function RecoveryCode({ code, onDone }) {
  return (
    <section aria-labelledby="recovery-title" className="card space-y-3">
      <h3 id="recovery-title" className="type-small font-semibold text-[var(--text)]">Your recovery code</h3>
      <div className="flex items-center gap-2">
        <code dir="ltr" data-testid="recovery-code"
          className="type-lead font-mono tracking-wider select-all text-[var(--text)] break-all">
          {code}
        </code>
        <CopyButton text={code} label="Copy" small />
      </div>
      <p className="type-small text-[var(--text-dim)]">
        Keep it somewhere safe, like a password manager or a note on paper. You need it to log in on another
        device, and it is shown only now. Each time you use it you get a new one.
      </p>
      {onDone && <PrimaryButton onClick={onDone}>I have saved it</PrimaryButton>}
    </section>
  )
}
