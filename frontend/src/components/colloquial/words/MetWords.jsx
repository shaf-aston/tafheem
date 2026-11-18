// The words a topic uses that an earlier topic already taught: kept to hand, apart from what is new
// here, so no word is ever taught as new twice. Folded away by default; open when nothing here is new.
import ArabicText from '../../ui/text/ArabicText'
import SpeakButton from '../../ui/buttons/SpeakButton'


export default function MetWords({ words, open = false }) {
  if (!words.length) return null
  return (
    <details open={open} className="group rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]">
      <summary className="cursor-pointer list-none flex items-center justify-between gap-3 px-4 py-3 min-h-11 type-ui font-medium text-[var(--text)] [&::-webkit-details-marker]:hidden">
        <span>Words you’ve met <span className="text-[var(--text-faint)] font-normal">· {words.length} from earlier topics</span></span>
        <span aria-hidden="true" className="text-[var(--text-faint)] transition-transform group-open:rotate-90">›</span>
      </summary>
      <ul className="flex flex-wrap gap-1.5 px-4 pb-4">
        {words.map((w) => (
          <li key={w.id} className="inline-flex items-center gap-1.5 rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--surface-hi)] ps-2.5 pe-1 py-0.5">
            <ArabicText size="sm" className="text-[var(--text)]">{w.arabic}</ArabicText>
            <span className="type-small text-[var(--text-dim)]">{w.english}</span>
            <SpeakButton text={w.arabic} />
          </li>
        ))}
      </ul>
    </details>
  )
}
