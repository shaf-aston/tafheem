/**
 * The one note a question may carry before it is answered: which Arabic is being
 * asked for, that its English came from a phrase, that an Urdu reader half knows
 * it. `note` is { text, why }.
 *
 * Two pieces, because the two screens need them in different places. A wide
 * screen shows the words as a pill in the corner with the reason under it. A
 * phone has no room to spare in a corner, so the pill is a small "i" and the
 * reason (NoteReason) is a line in the flow under the heading, where it pushes
 * the card down instead of covering the word. Either way the note is one tap
 * from its reason, never title-only: a tooltip cannot be reached on touch.
 *
 * Controlled, so the card that owns the question owns whether it is open and a
 * new question starts it closed.
 */
export default function NoteBadge({ note, open, onToggle }) {
  return (
    <div className="absolute end-0 top-0 flex flex-col items-end gap-1">
      <button
        type="button"
        title={note.why}
        aria-label={note.text}
        aria-expanded={open}
        onClick={onToggle}
        className="type-tiny text-[var(--text-faint)] hover:text-[var(--text-dim)] rounded-full border
          border-[var(--border)] transition-colors px-2 py-0.5
          max-sm:relative max-sm:size-6 max-sm:p-0 max-sm:grid max-sm:place-items-center
          max-sm:after:absolute max-sm:after:-inset-2 max-sm:after:content-['']"
      >
        <span className="max-sm:hidden">{note.text}</span>
        <span aria-hidden="true" className="sm:hidden font-semibold italic">i</span>
      </button>
      {open && <p className="max-sm:hidden type-small text-[var(--text-faint)] max-w-[14rem] text-end">{note.why}</p>}
    </div>
  )
}

/** The phone's reason line: in the flow under the heading, saying the note and why. */
export function NoteReason({ note, open }) {
  return open && (
    <p className="sm:hidden type-small text-[var(--text-faint)] text-center">
      <span className="font-semibold text-[var(--text-dim)]">{note.text}. </span>
      {note.why}
    </p>
  )
}
