// A phrase's picture and its words, shared by the mosaic tile and the sheet.
import ArabicText from '../../ui/ArabicText'
import PhrasePicture from './PhrasePicture'

export const FOCUS = 'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--primary)]'

const HUES = ['--primary', '--success', '--warn', '--danger']
const TINT_PERCENT = 20
const SCRIM_PERCENT = 94

const tint = (i) =>
  `radial-gradient(120% 90% at 20% 0%, color-mix(in srgb, var(${HUES[i % HUES.length]}) ${TINT_PERCENT}%, var(--surface-hi)), var(--surface) 75%)`

// Solid behind every line of the words, however many they wrap to, fading only
// across the top padding: Arabic never sits on a busy photo.
const SCRIM = `linear-gradient(to top, color-mix(in srgb, var(--bg) ${SCRIM_PERCENT}%, transparent) calc(100% - 2.5rem), transparent)`

// A photo fills the tile with the words over its foot; a drawing (an emoji .svg)
// sits above the words instead, so the Arabic never lies across it.
export default function Face({ phrase, index, arabicSize = 'base', showEnglish = true, numbered = true, className = '' }) {
  const drawn = phrase.image?.endsWith('.svg')
  const words = (
    <>
      <ArabicText as="p" size={arabicSize} className="text-[var(--text)]">{phrase.arabic}</ArabicText>
      {showEnglish && <p className="type-micro text-[var(--text-dim)] truncate">{phrase.english}</p>}
    </>
  )
  return (
    <div className={`relative overflow-hidden ${drawn ? 'flex flex-col bg-[var(--surface-hi)]' : ''} ${className}`}>
      {drawn
        ? <PhrasePicture phrase={phrase} className="flex-1 min-h-0 w-full pt-6!" />
        : <PhrasePicture phrase={phrase} className="absolute inset-0 w-full h-full" />}
      {!phrase.image && <div aria-hidden="true" className="absolute inset-0" style={{ background: tint(index) }} />}
      {numbered && <span className="absolute top-2 start-2 px-1.5 rounded bg-[var(--surface)]/85 type-micro tabular-nums text-[var(--text-dim)]">
        {String(index + 1).padStart(2, '0')}
      </span>}
      {drawn
        ? <div className="relative px-3 pb-3 text-center">{words}</div>
        : <div className="absolute inset-x-0 bottom-0 px-3 pb-3 pt-10 text-center" style={{ background: SCRIM }}>{words}</div>}
    </div>
  )
}
