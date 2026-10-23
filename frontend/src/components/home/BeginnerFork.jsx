/**
 * Home's first visit: two ways in, side by side. New to Arabic → Grow's Basics, straight into its first
 * lesson (ال, "the"); able to read already → the first fixed tab, as Home offered before. Shown only while
 * nothing is on the journey (HomePanel's `first`), so it is gone after the first step either way.
 */
import ArabicText from '../ui/ArabicText'
import PrimaryButton from '../ui/PrimaryButton'
import Tile from '../ui/Tile'

export const BASICS_LESSON = 'basics/lesson'

function Way({ accent, arabic, title, blurb, go, onClick }) {
  return (
    <Tile as="div" variant="lead" accent={accent} className="flex flex-col">
      <div className="flex items-center gap-3 flex-1">
        <ArabicText size="lg" style={{ color: accent }}>{arabic}</ArabicText>
        <div className="min-w-0">
          <p className="font-semibold">{title}</p>
          <p className="type-small text-[var(--text-dim)]">{blurb}</p>
        </div>
      </div>
      <PrimaryButton accent={accent} onClick={onClick}>{go} →</PrimaryButton>
    </Tile>
  )
}

export default function BeginnerFork({ copy, basicsAccent, reader, readerAccent, onGo }) {
  return (
    <section aria-labelledby="home-fork" className="space-y-2">
      <h3 id="home-fork" className="eyebrow eyebrow-lg">{copy['fork-label']}</h3>
      <div className="grid gap-3 sm:grid-cols-2">
        <Way accent={basicsAccent} arabic="ال" title={copy['new-title']} blurb={copy['new-blurb']} go={copy['new-go']}
          onClick={() => onGo('grow', BASICS_LESSON)} />
        <Way accent={readerAccent} arabic={reader.arabic} title={copy['reader-title']} blurb={reader.blurb} go={copy['first-go']}
          onClick={() => onGo(reader.id)} />
      </div>
    </section>
  )
}
