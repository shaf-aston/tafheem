/**
 * "Your Arabic": the learner's level as a three-way choice, in Settings, the profile and the sign-up sheet. Free to
 * change until the answers settle it (lib/learner/learnerLevel.js); then it shows the level and the answers that set it.
 */
import { fill } from '../../lib/shell/homeCopy'
import { LEVEL_COPY, LEVELS, levelOf } from '../../lib/learner/learnerLevel'
import { useLearnerLevel } from '../../lib/learner/useLearnerLevel'
import Segmented from '../ui/Segmented'

const OPTIONS = LEVELS.map((level) => ({ id: level.id, label: level.label }))

export default function LevelSetting({ accent = 'var(--primary)', hint = true }) {
  const { level, settled, basis, choose, guest } = useLearnerLevel()
  return (
    <div className="space-y-2">
      <p className="type-small font-semibold text-[var(--text)]" id="level-setting">{LEVEL_COPY.label}</p>
      {settled ? (
        <p className="type-small text-[var(--text-dim)]">
          <b className="text-[var(--text)]">{levelOf(level).label}</b>
          {' · '}
          {fill(LEVEL_COPY.settled, {
            share: Math.round(100 * basis.share), n: basis.answers, proof: levelOf(basis.id)['proof-label'],
          })}
        </p>
      ) : (
        <>
          <Segmented fill label={LEVEL_COPY.label} options={OPTIONS} value={level} accent={accent} onChange={choose} />
          {hint && <p className="type-small text-[var(--text-faint)]">{guest ? `${LEVEL_COPY.help} ${LEVEL_COPY.guest}` : LEVEL_COPY.help}</p>}
        </>
      )}
    </div>
  )
}
