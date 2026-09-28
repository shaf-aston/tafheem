// A phrase's picture and its words, shared by the mosaic tile and the sheet.
import ArabicText from '../ui/ArabicText'
import PhrasePicture from './PhrasePicture'

export const FOCUS = 'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--primary)]'

const HUES = ['--primary', '--success', '--warn', '--danger']
const TINT_PERCENT = 20
const SCRIM_PERCENT = 94

const tint = (i) =>
  `radial-gradient(120% 90% at 20% 0%, color-mix(in srgb, var(${HUES[i % HUES.length]}) ${TINT_PERCENT}%, var(--surface-hi)), var(--surface) 75%)`

const SCRIM = `linear-gradient(to top, color-mix(in srgb, var(--bg) ${SCRIM_PERCENT}%, transparent) 25%, transparent)`

export default function Face({ phrase, index, arabicSize = 'base', showEnglish = true, className = '' }) {
  return (
    <div className={`relative overflow-hidden ${className}`}>
      <PhrasePicture phrase={phrase} className="absolute inset-0 w-full h-full" />
      {!phrase.image && <div aria-hidden="true" className="absolute inset-0" style={{ background: tint(index) }} />}
      <span className="absolute top-2 start-3 type-micro tabular-nums text-[var(--text-faint)]">
        {String(index + 1).padStart(2, '0')}
      </span>
      <div className="absolute inset-x-0 bottom-0 px-3 pb-3 pt-10 text-center" style={{ background: SCRIM }}>
        <ArabicText as="p" size={arabicSize} className="text-[var(--text)]">{phrase.arabic}</ArabicText>
        {showEnglish && <p className="type-micro text-[var(--text-dim)] truncate">{phrase.english}</p>}
      </div>
    </div>
  )
}
