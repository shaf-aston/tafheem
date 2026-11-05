import { useRef } from 'react'

import { MISSED, WAITING } from '../../lib/recite/follow'
import { LOOK, SHOWN } from '../../lib/recite/reciteColors'
import { sameSpokenWord } from '../../lib/text/arabicText'

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
export default function RecitedWord({ word, at, ayah, recite, accent, cover, onStartAt }) {
  const anchor = useRef(null)
  const mark = recite.words[at] ?? { state: WAITING, heard: '' }
  // A word that was asked for rather than said. It is not one of the follower's
  // states, so it is read here and never written back into the marks.
  const wasShown = recite.shown?.has(at) && mark.state === WAITING
  const look = wasShown ? SHOWN : LOOK[mark.state]
  const missed = mark.state === MISSED
  const here = at === recite.at
  const added = recite.extras.filter((extra) => extra.after === at)
  const reached = mark.state !== WAITING
  const wrote = reached && mark.said && !sameSpokenWord(mark.said, word) ? mark.said : ''
  const opened = recite.open?.at === at
  // A covered word shows nothing until it has been reached, right or wrong, or
  // asked for. The cover is the word itself drawn in no colour on a soft block
  // (styles/recite.css), so it is exactly the word's size and the page never
  // moves when a word is said: its ink fades in where the block was.
  const covered = cover && mark.state === WAITING && !wasShown
  const state = wasShown ? 'shown' : missed ? 'missed' : mark.state === WAITING ? 'waiting' : 'said'

  const printed = (
    <ArabicText
      size="lg"
      className="recite-word"
      data-state={state}
      data-covered={covered ? '' : undefined}
      data-here={here ? '' : undefined}
      aria-hidden={covered || undefined}
      title={covered ? undefined : look?.label}
      style={{ '--look': look?.colour, '--here': accent }}
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
            data-at={at}
            onClick={() => (reached ? recite.setOpen(opened ? null : { at }) : onStartAt(at))}
            title={reached ? 'what the ear made of this word' : 'start reciting from here'}
            aria-label={reached ? `${word}, ${look?.label}, show details` : covered ? 'a word to say from memory' : `start reciting from ${word}`}
            aria-expanded={reached ? opened : undefined}
            className="inline-flex items-baseline bg-transparent p-0 cursor-pointer rounded-[var(--radius-sm)]
              focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--c)]/40"
          >
            {printed}
          </button>
          {!mark.heard && wrote && (
            // What the ear wrote, when it is not the page's word but the mark
            // was not red. It hangs under the word and takes no room, so the
            // line never re-wraps when it arrives (styles/recite.css): a
            // reciter can always check what the ear heard, and the page holds
            // still while they do.
            <ArabicText
              size="sm"
              aria-hidden
              title="what the ear wrote; press the word to hear yourself"
              className="recite-wrote"
            >
              {wrote}
            </ArabicText>
          )}
          {opened && <MarkCard ayah={ayah} at={at} recite={recite} anchor={anchor} onStartAt={onStartAt} />}
        </span>
      ) : printed}
      {mark.heard && (
        <ArabicText
          size="sm"
          title="what the microphone heard"
          style={{ color: look?.colour, borderColor: look?.colour }}
          className="recite-heard border rounded-[var(--radius-sm)] px-1.5"
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
          className="recite-heard border border-dashed rounded-[var(--radius-sm)] px-1.5"
        >
          {extra.heard}
        </ArabicText>
      ))}
    </>
  )
}
