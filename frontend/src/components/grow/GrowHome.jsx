/**
 * Grow's home: level, streak, daily goal, today's lesson, every world (unbuilt ones shown as coming).
 */
import { GOAL, GOALS, rankOf, shareOf } from '../../lib/rewards'
import { sayIn } from '../../lib/say'
import { useRemembered } from '../../lib/useRemembered'
import ArabicText from '../ui/ArabicText'
import PrimaryButton from '../ui/PrimaryButton'
import SectionHeader from '../ui/SectionHeader'

const say = sayIn('en')

/** Level, streak and goal; for a guest, a log-in hint. */
function Growth({ rewards }) {
  if (!rewards) {
    return <p className="grow-hint">{say('Log in to keep your XP, level and streak on any device.')}</p>
  }
  const rank = rankOf(rewards.level)
  return (
    <dl className="grow-stats">
      <div className="grow-stat grow-stat-wide">
        <dt>{say('Level {level}', { level: rewards.level })}</dt>
        <dd>
          <span>{rank.en} <ArabicText size="sm">{rank.ar}</ArabicText></span>
          <span className="grow-lesson-bar" aria-hidden="true"><i style={{ width: `${100 * shareOf(rewards)}%` }} /></span>
          <span className="grow-stat-small tabular-nums">{say('{into} / {need} XP to the next level', rewards)}</span>
        </dd>
      </div>
      <div className="grow-stat">
        <dt>{say('Streak')}</dt>
        <dd className="tabular-nums">{rewards.streak === 1 ? say('1 day') : say('{n} days', { n: rewards.streak })}</dd>
      </div>
      <Goal xpToday={rewards.xpToday} />
    </dl>
  )
}

/** Today's XP against the picked goal. */
function Goal({ xpToday }) {
  const [picked, pick] = useRemembered('grow-goal', GOALS, GOAL)
  const goal = Number(picked)
  const met = xpToday >= goal
  return (
    <div className="grow-stat" data-met={met ? '' : undefined}>
      <dt>{say('Daily goal')}</dt>
      <dd>
        <span className="tabular-nums">{met ? say('Met · {xp} XP', { xp: xpToday }) : say('{xp} / {goal} XP', { xp: xpToday, goal })}</span>
        <span className="grow-lesson-bar" aria-hidden="true"><i style={{ width: `${100 * Math.min(1, xpToday / goal)}%` }} /></span>
        <span className="grow-goals" role="radiogroup" aria-label={say('Daily goal')}>
          {GOALS.map((each) => (
            <button key={each} type="button" role="radio" aria-checked={each === picked} className="grow-goal"
              onClick={() => pick(each)}>
              {each}
            </button>
          ))}
        </span>
      </dd>
    </div>
  )
}

/** Today's words lesson, with the next hadith and prayer step beside it. */
function Today({ words, hadith, prayer, accent, onStart, onPrayer }) {
  const empty = words.ready && !words.fresh && !words.dueCount
  const nextHadith = hadith.ready && (hadith.next.fresh[0] ?? hadith.next.reviews[0])
  return (
    <section className="grow-today" style={{ '--w': accent }} aria-labelledby="grow-today-h">
      <p className="grow-today-kicker">{say('Today · about 5 minutes')}</p>
      <h3 id="grow-today-h">{say('Keep your garden growing')}</h3>
      {words.ready && (
        <p className="grow-today-holds tabular-nums">
          {say('{fresh} new words · {due} to review', { fresh: words.next.fresh.length, due: words.next.reviews.length })}
        </p>
      )}
      <PrimaryButton accent={accent} disabled={!words.ready || empty} onClick={() => onStart('words')}>
        {empty ? say('Every word learnt and nothing due') : say('Start')}
      </PrimaryButton>
      {nextHadith && (
        <button type="button" className="grow-today-side" onClick={() => onStart('hadith')}>
          {say('Hadith {n} of 42: {line}', { n: nextHadith.n, line: nextHadith.key.en })}
        </button>
      )}
      {prayer.next && (
        <button type="button" className="grow-today-side" onClick={onPrayer}>
          {say('Next prayer step: {title}', { title: prayer.next.title })}
        </button>
      )}
    </section>
  )
}

/** One world's tile. */
function WorldTile({ world, status, share, onOpen }) {
  return (
    <button
      type="button"
      className="grow-world-tile"
      style={{ '--w': world.accent }}
      disabled={!world.live}
      onClick={() => onOpen(world.id)}
      aria-label={`${world.name}, ${world.live ? status : say('coming soon')}`}
    >
      <ArabicText size="lg" className="grow-tile-ar">{world.arabic}</ArabicText>
      <span className="grow-tile-name">{world.name}</span>
      <span className="grow-tile-status">{world.live ? status : say('Coming soon')}</span>
      <span className="grow-lesson-bar" aria-hidden="true"><i style={{ width: `${100 * (share ?? 0)}%` }} /></span>
    </button>
  )
}

const stageStatus = (state) => (state.ready
  ? { status: say('Stage {n} · {into} of {need}', { n: state.stage.stage + 1, ...state.stage }), share: state.stage.into / state.stage.need }
  : { status: say('Loading…'), share: 0 })

export default function GrowHome({ worlds, rewards, lessons, prayer, onOpen, onStart }) {
  const statusOf = {
    ...Object.fromEntries(Object.entries(lessons).map(([id, state]) => [id, stageStatus(state)])),
    prayer: prayer.done.total
      ? { status: say('{learnt} of {total} steps learnt', prayer.done), share: prayer.done.learnt / prayer.done.total }
      : { status: say('Loading…'), share: 0 },
  }
  const accentOf = (id) => worlds.find((world) => world.id === id)?.accent
  return (
    <div className="grow-home">
      <SectionHeader title="Grow!" arabic="نَبَات" subtitle={say('A little every day, in every part of the app.')} />
      <Growth rewards={rewards} />
      <Today words={lessons.words} hadith={lessons.hadith} prayer={prayer} accent={accentOf('words')} onStart={onStart}
        onPrayer={() => onOpen('prayer')} />
      <h3 className="grow-worlds-h">{say('Worlds')}</h3>
      <div className="grow-worlds">
        {worlds.map((world) => (
          <WorldTile key={world.id} world={world} {...(statusOf[world.id] ?? {})} onOpen={onOpen} />
        ))}
      </div>
    </div>
  )
}
