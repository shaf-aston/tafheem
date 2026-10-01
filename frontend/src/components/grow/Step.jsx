/**
 * The two circles on the map. A step is a leaf to say or a square to do, a
 * flower once learnt; a group's bud wears a ring for how much of it is learnt.
 * Pressing either hands a step up; the bud hands up its next one.
 */
import { byHand } from '../../lib/growKinds'
import { sayIn } from '../../lib/say'
import ArabicText from '../ui/ArabicText'
import Mascot from '../ui/Mascot'
import MicMark from '../ui/MicMark'
import { Flower, GroupIcon, StateIcon } from './icons'

const say = sayIn('en')
const WORDS = { learnt: say('learnt'), started: say('in progress'), open: say('ready to start'), locked: say('locked') }

/** One step. `label` replaces its title, for a group of one step that is named by its group. */
export function Step({ one, group, k, mood, label, onPress }) {
  const { step, state, now } = one
  const act = byHand(step)
  return (
    <>
      <span className="grow-nw">
        <button
          type="button"
          className={`grow-node ${act ? 'grow-act' : `grow-leaf${k % 2 ? ' grow-alt' : ''}`}${now ? ' grow-pulse' : ''}`}
          data-s={state}
          data-now={now ? '' : undefined}
          disabled={state === 'locked'}
          aria-label={`${step.title}, ${WORDS[state]}`}
          onClick={(event) => onPress(step, event.currentTarget, state, group)}
        >
          <span className="grow-in"><StateIcon state={state} figure={act ? group.icon : null} /></span>
          {!act && state !== 'learnt' && <MicMark size={12} className="grow-say" />}
        </button>
        {now && <Mascot place="map" mood={mood} className="grow-qalam" />}
      </span>
      {label ?? <span className="grow-lbl" data-s={state} data-now={now ? '' : undefined}>{step.title}</span>}
    </>
  )
}

/** A group's name under its circle. */
export function GroupLabel({ group }) {
  return (
    <span className="grow-gl">
      {group.title}
      {group.arabic && <ArabicText size="sm" className="grow-gl-ar">{group.arabic}</ArabicText>}
    </span>
  )
}

export function Bud({ one, onPress }) {
  const { group, steps, state, learnt } = one
  const next = steps.find((each) => each.state !== 'learnt' && each.state !== 'locked') ?? steps[0]
  const fraction = learnt / steps.length
  return (
    <button
      type="button"
      className="grow-node grow-gnode"
      data-s={state}
      disabled={state === 'locked'}
      aria-label={`${group.title}, ${learnt} of ${steps.length} ${say('learnt')}`}
      onClick={(event) => onPress(next.step, event.currentTarget, next.state, group)}
    >
      {state !== 'locked' && (
        <svg viewBox="0 0 100 100" className="grow-ring" aria-hidden="true">
          <circle className="grow-ring-t" cx="50" cy="50" r="46" />
          {fraction > 0 && <circle className="grow-ring-f" cx="50" cy="50" r="46" pathLength="1" strokeDasharray={`${fraction} 1`} transform="rotate(-90 50 50)" />}
        </svg>
      )}
      <span className="grow-in">{state === 'learnt' ? <Flower /> : <GroupIcon name={group.icon} />}</span>
      <span className="grow-cnt" aria-hidden="true">{learnt}/{steps.length}</span>
    </button>
  )
}
