import { useRef } from 'react'

import { LOOK, SHOWN } from '../../lib/recite/reciteColors'

import ArabicText from '../ui/text/ArabicText'
import MarkCard from './MarkCard'

/**
 * One word of the page while it is being recited.
 *
 * Four things can be true of it, and each looks different because each means
 * something different: not reached yet, said and right, said and not sure, said
 * and wrong. A word never said at all is outlined rather than coloured in,
 * because there is nothing there to colour.
 *
 * What came back sits beside the word on the same line, never under it: under
 * it is where it was first put and it was too hard to see.
 *
 * A word that has been reached opens its card when pressed (MarkCard); one not
 * yet reached still starts the recitation there. An open card stays open if its
 * word flips back to waiting as a later reading lands.
 */
export default function RecitedWord({ word, at, ayah, recite, accent, coverWidth, onStartAt }) {
  const anchor = useRef(null)
  const mark = recite.words[at] ?? { state: 'waiting', heard: '' }
  // A word that was asked for rather than said. It is not one of the follower's
  // states, so it is read here and never written back into the marks.
  const wasShown = recite.shown?.has(at) && mark.state === 'waiting'
  const look = wasShown ? SHOWN : LOOK[mark.state]
  const missed = mark.state === 'missed'
  const here = at === recite.at
  const added = recite.extras.filter((extra) => extra.after === at)
  const reached = mark.state !== 'waiting'
  const opened = recite.open?.at === at
  // A covered word shows nothing until it has been reached, right or wrong, or
  // asked for. Every cover on a line is the same width, taken from the longest
  // word among them, because a cover the size of its own word gives it away.
  const covered = coverWidth && mark.state === 'waiting' && !wasShown

  const printed = covered ? (
    // A soft block where the word sits, rather than a bare underline: a page
    // of underlines read as empty, a page of blocks reads as words hidden.
    <span
      aria-label="a word to say from memory"
      className="inline-block align-middle rounded-[var(--radius-sm)] bg-[var(--surface-hi)] border transition-colors"
      style={{
        width: `${coverWidth}ch`,
        height: '1.1em',
        borderColor: here ? accent : 'var(--border)',
      }}
    />
  ) : (
    <ArabicText
      size="lg"
      title={wasShown ? SHOWN.label : look?.label}
      style={{
        color: look?.colour,
        // Where the reciter is, so the eye finds its place on a full page.
        boxShadow: here ? `0 2px 0 ${accent}` : undefined,
        // Dashed, so a word you were given never reads as a word you said,
        // even to somebody who cannot tell the two greys apart.
        ...(wasShown ? { borderBottom: '1px dashed var(--text-faint)' } : {}),
        ...(missed ? { border: '1px solid var(--danger)', borderRadius: '6px', padding: '0 4px' } : {}),
      }}
    >
      {word}
    </ArabicText>
  )

  return (
    <>
      {/* The page is the control: pressing a word starts the recitation there,
          or once it is reached shows what the ear made of it. A button rather
          than a click handler on the text, so it is reachable by keyboard and
          announces itself, and it carries no look of its own. */}
      {onStartAt ? (
        <span ref={anchor} className="relative inline-flex items-baseline">
          <button
            type="button"
            data-word=""
            onClick={() => (reached ? recite.setOpen(opened ? null : { at }) : onStartAt(at))}
            title={reached ? 'what the ear made of this word' : 'start reciting from here'}
            aria-label={reached ? `${word}, ${look?.label}, show details` : `start reciting from ${word}`}
            aria-expanded={reached ? opened : undefined}
            className="inline-flex items-baseline bg-transparent p-0 cursor-pointer rounded-[var(--radius-sm)]
              focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--c)]/40"
          >
            {printed}
          </button>
          {opened && <MarkCard ayah={ayah} at={at} recite={recite} anchor={anchor} onStartAt={onStartAt} />}
        </span>
      ) : printed}
      {mark.heard && (
        <ArabicText
          size="sm"
          title="what the microphone heard"
          style={{ color: look?.colour, borderColor: look?.colour }}
          className="border rounded-[var(--radius-sm)] px-1.5"
        >
          {`← ${mark.heard}`}
        </ArabicText>
      )}
      {added.map((extra, i) => (
        <ArabicText
          key={`${i}:${extra.heard}`}
          size="sm"
          title="said, and not in the book"
          style={{ color: 'var(--danger)', borderColor: 'var(--danger)' }}
          className="border border-dashed rounded-[var(--radius-sm)] px-1.5"
        >
          {extra.heard}
        </ArabicText>
      ))}
    </>
  )
}
