/**
 * Home's first visit: how much Arabic do you know? Three rows (levels.json), and one tap on a row is both the answer
 * and the start: the level is kept (lib/learner/useLearnerLevel.js) and its first place opens. A level already chosen (at
 * sign-up, on another device) is marked. Shown only while nothing is on the journey (HomePanel's `first`).
 */
import { LEVELS } from '../../lib/learner/learnerLevel'
import { useLearnerLevel } from '../../lib/learner/useLearnerLevel'
import { colorFor } from '../../theme'
import ArabicText from '../ui/text/ArabicText'
import Tile from '../ui/display/Tile'

export default function LevelPicker({ copy, onGo }) {
  const { chosen, choose } = useLearnerLevel()
  const pick = (level) => {
    choose(level.id)
    onGo(...level.start)
  }
  return (
    <section aria-labelledby="home-fork" className="space-y-2">
      <h3 id="home-fork" className="eyebrow eyebrow-lg">{copy['fork-label']}</h3>
      <div className="grid gap-2">
        {LEVELS.map((level) => {
          const accent = colorFor('world', level.grow)
          const mine = level.id === chosen
          return (
            <Tile key={level.id} variant="chip" accent={accent} aria-current={mine || undefined}
              className={`py-3 ${mine ? 'border-[var(--c)]' : ''}`} onClick={() => pick(level)}>
              <span className="flex items-center gap-3 min-w-0">
                <ArabicText size="lg" className="w-14 shrink-0 text-center" style={{ color: accent }}>{level.arabic}</ArabicText>
                <span className="grid min-w-0">
                  <span className="font-semibold">
                    {level.title}
                    <span className="type-small font-normal text-[var(--text-faint)]"> · {level.label}</span>
                    {mine && <span className="type-small font-semibold" style={{ color: accent }}> · {copy['fork-yours']}</span>}
                  </span>
                  <span className="type-small text-[var(--text-dim)]">{level.blurb}</span>
                </span>
              </span>
              <span aria-hidden="true" className="text-xl" style={{ color: accent }}>›</span>
            </Tile>
          )
        })}
      </div>
      <p className="type-small text-[var(--text-faint)]">{copy['fork-hint']}</p>
    </section>
  )
}
