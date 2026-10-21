import { colorFor } from '../../theme'
import { kindOf, opening, whereOf, wordFlags, wordsAt } from '../../lib/similar'
import copy from '../../similar.json'

import ArabicText from '../ui/ArabicText'
import { TwinRow } from '../ui/TwinCard'

const MINE = colorFor('similar', 'mine')
const TWIN = colorFor('similar', 'twin')

/** One verse on its own card, its differing words in its own colour. */
function Verse({ verse, spans, color }) {
  const words = verse.text.split(/\s+/).filter(Boolean)
  return (
    <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--bg)] p-3 sm:p-4 space-y-1">
      <p className="type-small font-semibold" style={{ color }}>{whereOf(verse.key)}</p>
      <TwinRow label="" words={words} flags={wordFlags(words.length, spans)} accent={color} />
    </div>
  )
}

/** One side of a difference: its words, or a quiet "nothing here". */
function Side({ verse, words, color, blank }) {
  return (
    <div className="rounded-[var(--radius-sm)] bg-[var(--surface-hi)] px-3 py-2">
      <p className="type-tiny font-semibold" style={{ color }}>{whereOf(verse.key)}</p>
      {words
        ? <ArabicText size="base" className="block text-[var(--text)]">{words}</ArabicText>
        : <p className="type-small italic text-[var(--text-faint)] text-right">{blank}</p>}
    </div>
  )
}

/**
 * Both verses stacked, then each difference side by side, then what follows each:
 * the page a pair is learnt from. A pair that reads the same has only the last,
 * and says so, because that is the whole tell.
 */
export default function Compare({ mine, partner }) {
  const kind = kindOf(partner.change_type)
  const same = partner.changes.length === 0
  return (
    <div className="space-y-3">
      <Verse verse={mine} spans={partner.changes.map((c) => c.self)} color={MINE} />
      <Verse verse={partner} spans={partner.changes.map((c) => c.other)} color={TWIN} />
      {same ? (
        <p className="type-small text-[var(--text-dim)]">{copy.same}</p>
      ) : (
        <>
          <h3 className="eyebrow pt-2">
            {copy.apart}
            {kind && <span className="ml-2 font-normal normal-case tracking-normal text-[var(--text-faint)]">· {kind}</span>}
          </h3>
          <div className="space-y-2">
            {partner.changes.map((change, i) => (
              <div key={i} className="grid grid-cols-2 gap-2">
                <Side verse={mine} words={wordsAt(mine.text, change.self)} color={MINE} blank={copy.nothing} />
                <Side verse={partner} words={wordsAt(partner.text, change.other)} color={TWIN} blank={copy.nothing} />
              </div>
            ))}
          </div>
        </>
      )}
      <h3 className="eyebrow pt-2">{copy.after}</h3>
      <div className="grid grid-cols-2 gap-2" data-similar-after="">
        <Side verse={mine} words={opening(mine.after)} color={MINE} blank={copy.end} />
        <Side verse={partner} words={opening(partner.after)} color={TWIN} blank={copy.end} />
      </div>
    </div>
  )
}
