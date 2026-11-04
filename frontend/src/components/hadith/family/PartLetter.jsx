/** A narration's letter (a, b, c) in a ring of the tab's colour; pressing it opens that hadith. */
export default function PartLetter({ part, accent, onOpen }) {
  return (
    <button
      type="button"
      onClick={onOpen}
      aria-label={`Open ${part}`}
      style={{ color: accent, borderColor: accent }}
      className="press type-tiny shrink-0 w-7 h-7 grid place-items-center rounded-full border"
    >
      {part}
    </button>
  )
}
