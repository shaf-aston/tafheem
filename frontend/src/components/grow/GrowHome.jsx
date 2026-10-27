/**
 * Grow's home: level, streak, daily goal, today's lesson with each world's next step, every world (unbuilt ones shown as coming).
 * Today leads with the book last studied (its next lesson, one tap away) once there is one, then the learner's level
 * (levels.json `grow`: a beginner's Basics, an advanced learner's Nahw), the Basics while begun on this device and with a
 * lesson to give, and the words lesson otherwise;
 * a book with questions due shows its review as a step too.
 * A guest's log-in nudge rides on the title line (SectionHeader `aside`).
 */
import { Fragment, useState } from 'react'

import { GOAL, GOALS, rankOf, shareOf } from '../../lib/learner/rewards'
import { REVIEW_SIZE } from '../../lib/grow/bookLesson'
import { LAST_BOOK, REVIEW } from '../../lib/grow/useBookWorld'
import { sayIn } from '../../lib/text/say'
import { useRemembered } from '../../lib/store/useRemembered'
import { levelOf } from '../../lib/learner/learnerLevel'
import { useLearnerLevel } from '../../lib/learner/useLearnerLevel'
import LogInButton from '../profile/LogInButton'
import Emblem from '../ui/display/Emblem'
import ArabicText from '../ui/text/ArabicText'
import PrimaryButton from '../ui/buttons/PrimaryButton'
import SectionHeader from '../ui/display/SectionHeader'
import { useReveal } from '../../lib/motion/useReveal'
import { useTilt } from '../../lib/motion/useTilt'

const say = sayIn('en')


/** What the stats are laid out with while the record is read: shown hidden (data-pending), so the worlds below stay put. */
const HELD = { level: 1, into: 0, need: 1, streak: 0, xpToday: 0 }

/** Level, streak and goal; nothing when the record could not be read. */
function Growth({ rewards: record, pending }) {
  if (!record && !pending) return null
  const rewards = record ?? HELD
  const rank = rankOf(rewards.level)
  return (
    <dl className="grow-stats" data-pending={record ? undefined : ''} aria-hidden={record ? undefined : true}>
      <div className="grow-stat grow-stat-wide rise-in">
        <dt>{say('Level {level}', { level: rewards.level })}</dt>
        <dd>
          <span>{rank.en} <ArabicText size="sm">{rank.ar}</ArabicText></span>
          <span className="grow-lesson-bar" aria-hidden="true"><i style={{ width: `${100 * shareOf(rewards)}%` }} /></span>
          <span className="grow-stat-small tabular-nums">{say('{into} / {need} XP to the next level', rewards)}</span>
        </dd>
      </div>
      <div className="grow-stat rise-in">
        <dt>{say('Streak')}</dt>
        <dd className="tabular-nums">
          {rewards.streak === 1 ? say('1 day') : say('{n} days', { n: rewards.streak })}
          <span className="grow-stat-small">{rewards.streak ? say('Come back tomorrow to keep it') : say('One lesson today starts it')}</span>
        </dd>
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
    <div className="grow-stat rise-in" data-met={met ? '' : undefined}>
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
    <button type="button" className="grow-next rise-in" style={{ '--w': world.accent }} onClick={onGo}>
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

/** The room for the next steps while the worlds load; they all appear at once (data-settling, styles/growWorlds.css), so the page below moves once, not per world. */
const NextSlot = () => <span className="grow-next grow-next-slot" aria-hidden="true" />

/** A lessons world with a lesson to give: words not yet met, or some due. */
const hasWork = (state) => state.ready && (state.fresh > 0 || state.dueCount > 0)

/**
 * Today's lesson: the last book's next one when there is one, else the Basics while begun here and with work to give,
 * else the words lesson; then every world's next step.
 */
function Today({ worldOf, lessons, books, onStart, onStartBook }) {
  // A phone shows three next steps until More is pressed (styles/growWorlds.css).
  const [more, setMore] = useState(false)
  // The button goes once pressed, so the focus moves on to the first step it showed.
  function showMore(event) {
    const list = event.currentTarget.previousElementSibling
    setMore(true)
    requestAnimationFrame(() => list.children[3]?.focus())
  }
  const [last] = useRemembered(LAST_BOOK, Object.keys(books), '')
  // The world the learner's level starts from (levels.json `grow`); none until a level is chosen.
  const leads = levelOf(useLearnerLevel().level)?.grow
  const { words, basics } = lessons
  const onBasics = (basics.begunHere || leads === 'basics') && !(basics.ready && !hasWork(basics))
  const main = onBasics ? basics : words
  const mainId = onBasics ? 'basics' : 'words'
  const empty = main.ready && !hasWork(main)
  const hadith = nextOf(lessons.hadith)
  const ayah = nextOf(lessons.quran)
  // Without words to start, a book leads even before one was studied.
  const open = (id) => books[id]?.ready && books[id].next
  // A level that starts from a book (advanced: Nahw) leads with it until another book is studied.
  const lead = open(last) ? last : open(leads) ? leads : words.error ? Object.keys(books).find(open) ?? null : null
  const lineOf = (state) => {
    if (state.ready) return say('{fresh} new {unit} · {due} to review', { fresh: state.next.fresh.length, unit: state.world.unit, due: state.next.reviews.length })
    return state.error ? say('Words could not load just now. The book worlds below still work.') : '\u00a0'
  }
  // The Basics and the words each show as a step whenever they are not the lesson above.
  const hero = lead ?? mainId
  const partOf = (book) => book.parts.find((part) => part.id === book.next.part)?.title
  const accent = worldOf(lead ?? mainId).accent
  const settling = [basics, words, ...Object.values(books), lessons.hadith, lessons.quran].some((state) => !state.ready && !state.error)
  return (
    <section className="grow-today rise-in" style={{ '--w': accent }} aria-labelledby="grow-today-h">
      <span className="grow-today-art" aria-hidden="true"><Emblem id={lead ?? mainId} /></span>
      {lead ? (
        <>
          <p className="grow-today-kicker">{say('Continue · {world}', { world: worldOf(lead).name })}</p>
          <h3 id="grow-today-h">{books[lead].next.title}</h3>
          <p className="grow-today-holds">{partOf(books[lead])}</p>
          <PrimaryButton accent={accent} onClick={() => onStartBook(lead, books[lead].next.id, books[lead].next.part)}>{say('Continue')}</PrimaryButton>
        </>
      ) : (
        <>
          <p className="grow-today-kicker">{say('Today · about 5 minutes')}</p>
          <h3 id="grow-today-h">{onBasics ? say('Your first steps') : say('Keep your garden growing')}</h3>
          <p className="grow-today-holds tabular-nums">{lineOf(main)}</p>
          <PrimaryButton accent={accent} disabled={!main.ready || empty} onClick={() => onStart(mainId)}>
            {empty ? say('Every word learnt and nothing due') : say('Start')}
          </PrimaryButton>
        </>
      )}
      <div className="grow-nexts" data-open={more ? '' : undefined} data-settling={settling ? '' : undefined}>
        {settling && <NextSlot />}
        {basics.ready && !basics.begunHere && hero !== 'basics' && (!leads || leads === 'basics') && (
          <NextStep world={worldOf('basics')} where={say('New to Arabic?')} line={say('Start with ال, “the”')} onGo={() => onStart('basics')} />
        )}
        {basics.begunHere && hero !== 'basics' && hasWork(basics) && (
          <NextStep world={worldOf('basics')} where={say('Your first steps')} line={lineOf(basics)} onGo={() => onStart('basics')} />
        )}
        {hero !== 'words' && hasWork(words) && (
          <NextStep world={worldOf('words')} where={say('Today’s words')} line={lineOf(words)} onGo={() => onStart('words')} />
        )}
        {Object.entries(books).map(([id, book]) => {
          if (!book.ready) return null
          return (
            <Fragment key={id}>
              {book.due.length > 0 && (
                <NextStep world={worldOf(id)} where={say('Review')}
                  line={book.due.length === 1 ? say('1 question due') : say('{n} questions due', { n: Math.min(book.due.length, REVIEW_SIZE) })}
                  onGo={() => onStartBook(id, REVIEW)} />
              )}
              {book.next && id !== lead && (
                <NextStep world={worldOf(id)} where={partOf(book)} line={book.next.title} onGo={() => onStartBook(id, book.next.id, book.next.part)} />
              )}
            </Fragment>
          )
        })}
        {hadith && (
          <NextStep world={worldOf('hadith')} where={say('{n} of 42', { n: hadith.n })} line={hadith.key.en} onGo={() => onStart('hadith')} />
        )}
        {ayah && (
          <NextStep world={worldOf('quran')} where={say('{surah}, ayah {n}', { surah: ayah.name_en, n: ayah.ayah })} line={ayah.english}
            onGo={() => onStart('quran')} />
        )}
      </div>
      <button type="button" className="grow-nexts-more" onClick={showMore}>{say('More for today')}</button>
    </section>
  )
}

/** One world's tile. */
function WorldTile({ world, status, share, index, onOpen }) {
  const [ref, reveal] = useReveal()
  const tilt = useTilt()
  return (
    <button
      ref={ref}
      type="button"
      {...tilt}
      className={`grow-world-tile e1 tilt ${reveal}`}
      style={{ '--w': world.accent, '--i': index }}
      disabled={!world.live}
      onClick={() => onOpen(world.id)}
      aria-label={`${world.name}, ${world.live ? status : say('coming soon')}`}
    >
      <Emblem id={world.id} size={52} />
      <ArabicText size="lg" className="grow-tile-ar">{world.arabic}</ArabicText>
      <span className="grow-tile-name">{world.name}</span>
      <span className="grow-tile-status">{world.live ? status : say('Coming soon')}</span>
      <span className="grow-lesson-bar" aria-hidden="true"><i style={{ width: `${100 * (share ?? 0)}%` }} /></span>
    </button>
  )
}

// A world that could not load says so, instead of loading for ever.
const waiting = (state) => ({ status: state.error ? say('Could not load') : say('Loading…'), share: 0 })

const stageStatus = (state) => (state.ready
  ? { status: say('Stage {n} · {into} of {need}', { n: state.stage.stage + 1, ...state.stage }), share: state.stage.into / state.stage.need }
  : waiting(state))

/** A book world's tile: lessons finished of those written so far. */
function bookStatus(state) {
  if (!state.ready) return waiting(state)
  const total = state.parts.reduce((sum, part) => sum + part.lessons.length, 0)
  const done = state.parts.reduce((sum, part) => sum + part.finished, 0)
  return { status: say('{done} of {total} lessons', { done, total }), share: total ? done / total : 0 }
}

/** A lesson left unfinished: one tap back in, above everything else. */
function Resume({ world, onResume }) {
  return (
    <section className="grow-today" style={{ '--w': world.accent }} aria-labelledby="grow-resume-h">
      <p className="grow-today-kicker">{say('Unfinished lesson')}</p>
      <h3 id="grow-resume-h">{world.name}</h3>
      <PrimaryButton accent={world.accent} onClick={onResume}>{say('Resume')}</PrimaryButton>
    </section>
  )
}

export default function GrowHome({ worlds, rewards, rewardsPending, guest, lessons, books, resume, onResume, onOpen, onStart, onStartBook }) {
  const statusOf = {
    ...Object.fromEntries(Object.entries(lessons).map(([id, state]) => [id, stageStatus(state)])),
    ...Object.fromEntries(Object.entries(books).map(([id, state]) => [id, bookStatus(state)])),
  }
  const worldOf = (id) => worlds.find((world) => world.id === id)
  return (
    <div className="grow-home">
      {/* No trail: Grow draws its own ways back (a world's back arrow, a lesson's ×), and its places are not words. */}
      <SectionHeader tab="grow" subtitle={say('A little every day, in every part of the app.')} history={false}
        aside={guest ? <LogInButton>{say('Log in to keep your XP on any device')}</LogInButton> : null} />
      {resume && <Resume world={worldOf(resume.id)} onResume={onResume} />}
      {/* Today's lesson first, where a phone's first screen shows it; the level, streak and goal under it. */}
      <Today worldOf={worldOf} lessons={lessons} books={books} onStart={onStart} onStartBook={onStartBook} />
      <Growth rewards={rewards} pending={rewardsPending} />
      <h3 className="grow-worlds-h">{say('Worlds')}</h3>
      <div className="grow-worlds">
        {worlds.map((world, index) => (
          <WorldTile key={world.id} world={world} index={index} {...(statusOf[world.id] ?? {})} onOpen={onOpen} />
        ))}
      </div>
    </div>
  )
}
