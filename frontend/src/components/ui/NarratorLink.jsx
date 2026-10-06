/**
 * A narrator's name where it stands in a text, with a faint dotted line under
 * it: tapping opens his sheet. The one look for a name that is a link, in the
 * hadith's words and in the chain drawing alike. Without an id it is plain text.
 */
export default function NarratorLink({ id, onOpen, children }) {
  if (id == null || !onOpen) return children
  return (
    <button
      type="button"
      onClick={() => onOpen(id)}
      className="press text-inherit underline underline-offset-4 decoration-dotted decoration-[var(--text-faint)] hover:decoration-[var(--text-dim)]"
    >
      {children}
    </button>
  )
}
