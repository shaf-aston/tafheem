/**
 * Grow's home: level, streak, daily goal, today's lesson with each world's next step, every world (unbuilt ones shown as coming).
 * A guest's log-in nudge rides on the title line (SectionHeader `aside`).
 */
import { useState } from 'react'

import { GOAL, GOALS, rankOf, shareOf } from '../../lib/rewards'
import { sayIn } from '../../lib/say'
import { useRemembered } from '../../lib/useRemembered'
import ProfileDialog from '../profile/ProfileDialog'
import ArabicText from '../ui/ArabicText'
import PrimaryButton from '../ui/PrimaryButton'
import SectionHeader from '../ui/SectionHeader'

const say = sayIn('en')

/** For a guest: one line offering the log-in, which opens the profile dialog. */
function LogInNudge() {
  const [open, setOpen] = useState(false)
  return (
    <>
      <button type="button" className="grow-login" onClick={() => setOpen(true)}>
        {say('Log in to keep your XP')}
      </button>
      {open && <ProfileDialog onClose={() => setOpen(false)} />}
    </>
  )
}

/** Level, streak and goal; nothing for a guest (the nudge is on the title line). */
function Growth({ rewards }) {
  if (!rewards) return null
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

/** One world's next step, under today's lesson: its name, where it is up to, the item itself. */
function NextStep({ world, where, line, onGo }) {
  return (
    <button type="button" className="grow-next" style={{ '--w': world.accent }} onClick={onGo}>
      <ArabicText className="grow-next-ar">{world.arabic}</ArabicText>
      <span className="grow-next-text">
        <b>{world.name} · {where}</b>
        <span>{line}</span>
      </span>
      <span className="grow-next-go" aria-hidden="true">›</span>
    </button>
  )
}

const nextOf = (state) => state?.ready && (state.next.fresh[0] ?? state.next.reviews[0])

/** A next-step card's room while its world loads, so nothing below jumps when it lands. */
const NextSlot = () => <span className="grow-next grow-next-slot" aria-hidden="true" />

/** Today's words lesson, then the next step in Fiqh, Hadith and Quran. */
function Today({ worldOf, lessons, books, onStart, onStartBook }) {
  const { words } = lessons
  const empty = words.ready && !words.fresh && !words.dueCount
  const hadith = nextOf(lessons.hadith)
  const ayah = nextOf(lessons.quran)
  const { fiqh } = books
  return (
    <section className="grow-today" style={{ '--w': worldOf('words').accent }} aria-labelledby="grow-today-h">
      <p className="grow-today-kicker">{say('Today · about 5 minutes')}</p>
      <h3 id="grow-today-h">{say('Keep your garden growing')}</h3>
      <p className="grow-today-holds tabular-nums">
        {words.ready ? say('{fresh} new words · {due} to review', { fresh: words.next.fresh.length, due: words.next.reviews.length }) : '\u00a0'}
      </p>
      <PrimaryButton accent={worldOf('words').accent} disabled={!words.ready || empty} onClick={() => onStart('words')}>
        {empty ? say('Every word learnt and nothing due') : say('Start')}
      </PrimaryButton>
      <div className="grow-nexts">
        {!fiqh.ready && <NextSlot />}
        {fiqh.next && (
          <NextStep world={worldOf('fiqh')} where={fiqh.parts.find((part) => part.id === fiqh.next.part)?.title} line={fiqh.next.title}
            onGo={() => onStartBook('fiqh', fiqh.next.id, fiqh.next.part)} />
        )}
        {!lessons.hadith.ready && <NextSlot />}
        {hadith && (
          <NextStep world={worldOf('hadith')} where={say('{n} of 42', { n: hadith.n })} line={hadith.key.en} onGo={() => onStart('hadith')} />
        )}
        {!lessons.quran.ready && <NextSlot />}
        {ayah && (
          <NextStep world={worldOf('quran')} where={say('{surah}, ayah {n}', { surah: ayah.name_en, n: ayah.ayah })} line={ayah.english}
            onGo={() => onStart('quran')} />
        )}
      </div>
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

/** A book world's tile: lessons finished of those written so far. */
function bookStatus(state) {
  if (!state.ready) return { status: say('Loading…'), share: 0 }
  const total = state.parts.reduce((sum, part) => sum + part.lessons.length, 0)
  const done = state.parts.reduce((sum, part) => sum + part.finished, 0)
  return { status: say('{done} of {total} lessons', { done, total }), share: total ? done / total : 0 }
}

export default function GrowHome({ worlds, rewards, lessons, books, onOpen, onStart, onStartBook }) {
  const statusOf = {
    ...Object.fromEntries(Object.entries(lessons).map(([id, state]) => [id, stageStatus(state)])),
    ...Object.fromEntries(Object.entries(books).map(([id, state]) => [id, bookStatus(state)])),
  }
  const worldOf = (id) => worlds.find((world) => world.id === id)
  return (
    <div className="grow-home">
      <SectionHeader title="Grow!" arabic="نَبَات" subtitle={say('A little every day, in every part of the app.')}
        aside={rewards ? null : <LogInNudge />} />
      <Growth rewards={rewards} />
      <Today worldOf={worldOf} lessons={lessons} books={books} onStart={onStart} onStartBook={onStartBook} />
      <h3 className="grow-worlds-h">{say('Worlds')}</h3>
      <div className="grow-worlds">
        {worlds.map((world) => (
          <WorldTile key={world.id} world={world} {...(statusOf[world.id] ?? {})} onOpen={onOpen} />
        ))}
      </div>
    </div>
  )
}
