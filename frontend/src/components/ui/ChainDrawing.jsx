/**
 * One hadith's chain drawn as a ladder: the narrator nearest the Prophet ﷺ at
 * the top, the author of the book at the foot, and on each rung the small
 * word that says how it was passed down (سمعت، حدّثنا، عن), in the colour of
 * how it was received.
 *
 * A chain the book split with ح grows branches: they rise from the author
 * side by side and join the main strand at the narrator both name. A strand
 * the books do not join anywhere stands on its own beside them, reaching only
 * the author, since that is all the text says. lib/hadithWords chainLinks
 * reads the chain; this only draws it. A name sunnah.com linked (lib/rijal
 * linked) is a ui/NarratorLink. A weak narrator (lib/weak, in `weak`) has his box
 * edged in the hadith.weak colour and his rank at its start corner. A link a
 * source puts in doubt (`linkPoints`) has its word dotted-underlined in that
 * colour with its letter beside it, the same letter the list prints.
 */
import { Fragment } from 'react'

import ArabicText from './ArabicText'
import NarratorLink from './NarratorLink'

/** A rung: a short line with the word that passed the hadith down it. `marks` are the letters of its doubtful links. */
function Rung({ link, marks = [], grow = false }) {
  return (
    <div className={`chain-line relative w-px min-h-7 ${grow ? 'flex-1' : ''}`}>
      {link?.term && (
        <ArabicText
          size="sm"
          className="absolute top-3.5 -translate-y-1/2 start-full ms-2 whitespace-nowrap opacity-80"
          style={{ color: link.way ? `var(--hadith-${link.way})` : 'var(--text-faint)' }}
        >
          {marks.length > 0 ? (
            <>
              <span className="underline decoration-dotted underline-offset-4 decoration-[var(--hadith-weak)]">{link.term}</span>
              <bdi dir="ltr" className="type-tiny tabular-nums ms-1 text-[var(--hadith-weak)]">{marks.join(',')}</bdi>
              <span className="sr-only">, weak link {marks.join(' and ')}</span>
            </>
          ) : link.term}
        </ArabicText>
      )}
    </div>
  )
}

function Narrator({ link, weak, onNarrator }) {
  const point = weak.find((p) => link.members.some((m) => m.note?.id === p.id))   // weak is weakest first
  return (
    <div className="relative max-w-[var(--sheet-narrator)]">
      {point && (
        <span
          aria-hidden="true"
          className="absolute -top-2 start-2 px-1 leading-none type-tiny tabular-nums bg-[var(--surface-hi)] text-[var(--hadith-weak)]"
        >
          <bdi dir="ltr">{point.label}</bdi>
        </span>
      )}
      <ArabicText
        size="base"
        className="block text-center leading-relaxed px-3 py-1 rounded-[var(--radius-md)]
          border border-[var(--border)] bg-[var(--surface-hi)] text-[var(--text)]"
        style={point ? { borderColor: 'var(--hadith-weak)' } : undefined}
      >
        <>
          <NarratorLink id={link.id} onOpen={onNarrator}>{link.name}</NarratorLink>
          {point && <span className="sr-only">, weak point {point.label}: {point.en}</span>}
        </>
      </ArabicText>
    </div>
  )
}

/** The letters of the doubtful links whose teacher is `link`: those that start where his name does. */
const marksOf = (link, linkPoints) => linkPoints.filter((p) => link?.ties?.some((t) => t.at === p.at && t.kind === p.kind)).map((p) => p.letter)

/** Narrators top down, each with the rung below it; the last rung reaches the foot. */
function Strand({ links, top = null, weak, linkPoints, onNarrator }) {
  return (
    <div className="flex flex-col items-center px-3">
      {top}
      {[...links].reverse().map((link, i, all) => (
        <Fragment key={`${link.name}-${i}`}>
          <Narrator link={link} weak={weak} onNarrator={onNarrator} />
          <Rung link={link} marks={marksOf(link, linkPoints)} grow={i === all.length - 1} />
        </Fragment>
      ))}
    </div>
  )
}

export default function ChainDrawing({ links, author, weak = [], linkPoints = [], onNarrator }) {
  const { main, branches } = links
  // Where the branches join: the highest narrator any of them meets.
  const fork = Math.max(0, ...branches.map((b) => b.at ?? 0))
  const joined = branches.filter((b) => fork && b.at === fork)
  const alone = branches.filter((b) => !joined.includes(b))
  const trunk = main.slice(fork)

  const tree = (
    <div className="flex flex-col items-center">
      <Strand links={fork ? trunk.slice(1) : trunk} weak={weak} linkPoints={linkPoints} onNarrator={onNarrator} />
      {fork > 0 && (
        <>
          <Narrator link={main[fork]} weak={weak} onNarrator={onNarrator} />
          <div className="chain-split chain-merge flex items-stretch">
            {joined.map((b, i) => <Strand key={i} links={b.links} top={<Rung link={b.join} marks={marksOf(b.join, linkPoints)} />} weak={weak} linkPoints={linkPoints} onNarrator={onNarrator} />)}
            <Strand links={main.slice(0, fork)} top={<Rung link={main[fork]} marks={marksOf(main[fork], linkPoints)} />} weak={weak} linkPoints={linkPoints} onNarrator={onNarrator} />
          </div>
        </>
      )}
    </div>
  )

  return (
    <div dir="rtl" className="flex flex-col items-center overflow-x-auto py-2">
      {alone.length ? (
        <div className="chain-merge flex items-stretch">
          {alone.map((b, i) => (
            <Strand
              key={i}
              links={b.links}
              weak={weak}
              linkPoints={linkPoints}
              onNarrator={onNarrator}
              top={b.at !== null && <span className="type-tiny text-[var(--text-faint)] mb-1" dir="ltr">joins at <ArabicText size="tiny">{main[b.at].name}</ArabicText></span>}
            />
          ))}
          <div className="flex flex-col items-center px-3">{tree}<Rung grow /></div>
        </div>
      ) : tree}
      <Rung />
      <span className="type-small px-3 py-1 rounded-full border border-[var(--border)] text-[var(--text-dim)]" dir="ltr">{author}</span>
    </div>
  )
}
