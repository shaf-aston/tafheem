/**
 * Grow's home: level, streak, daily goal, today's lesson with each world's next step, every world (unbuilt ones shown as coming).
 * Today leads with the book last studied (its next lesson, one tap away) once there is one, and the words lesson otherwise;
 * a book with questions due shows its review as a step too.
 * A guest's log-in nudge rides on the title line (SectionHeader `aside`).
 */
import { Fragment } from 'react'

import { GOAL, GOALS, rankOf, shareOf } from '../../lib/rewards'
import { REVIEW_SIZE } from '../../lib/bookLesson'
import { LAST_BOOK, REVIEW } from '../../lib/useBookWorld'
import { sayIn } from '../../lib/say'
import { useRemembered } from '../../lib/useRemembered'
import LogInButton from '../profile/LogInButton'
import Emblem from '../ui/Emblem'
import ArabicText from '../ui/ArabicText'
import PrimaryButton from '../ui/PrimaryButton'
import SectionHeader from '../ui/SectionHeader'
import { useReveal } from '../../lib/useReveal'
import { useTilt } from '../../lib/useTilt'

const say = sayIn('en')


/** Level, streak and goal; nothing for a guest (the nudge is on the title line). */
function Growth({ rewards }) {
  if (!rewards) return null
  const rank = rankOf(rewards.level)
  return (
    <dl className="grow-stats">
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

/** A next-step card's room while its world loads, so nothing below jumps when it lands. */
const NextSlot = () => <span className="grow-next grow-next-slot" aria-hidden="true" />

/** Today's lesson: the last book's next one when there is one, else the words lesson; then every world's next step. */
function Today({ worldOf, lessons, books, onStart, onStartBook }) {
  const [last] = useRemembered(LAST_BOOK, Object.keys(books), '')
  const { words } = lessons
  const empty = words.ready && !words.fresh && !words.dueCount
  const hadith = nextOf(lessons.hadith)
  const ayah = nextOf(lessons.quran)
  // Without words to start, a book leads even before one was studied.
  const open = (id) => books[id]?.ready && books[id].next
  const lead = open(last) ? last : words.error ? Object.keys(books).find(open) ?? null : null
  let wordsLine = '\u00a0'
  if (words.ready) wordsLine = say('{fresh} new words · {due} to review', { fresh: words.next.fresh.length, due: words.next.reviews.length })
  else if (words.error) wordsLine = say('Words could not load just now. The book worlds below still work.')
  const partOf = (book) => book.parts.find((part) => part.id === book.next.part)?.title
  const accent = worldOf(lead ?? 'words').accent
  return (
    <section className="grow-today rise-in" style={{ '--w': accent }} aria-labelledby="grow-today-h">
      <span className="grow-today-art" aria-hidden="true"><Emblem id={lead ?? 'words'} /></span>
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
          <h3 id="grow-today-h">{say('Keep your garden growing')}</h3>
          <p className="grow-today-holds tabular-nums">{wordsLine}</p>
          <PrimaryButton accent={accent} disabled={!words.ready || empty} onClick={() => onStart('words')}>
            {empty ? say('Every word learnt and nothing due') : say('Start')}
          </PrimaryButton>
        </>
      )}
      <div className="grow-nexts">
        {lead && words.ready && !empty && (
          <NextStep world={worldOf('words')} where={say('Today’s words')} line={wordsLine} onGo={() => onStart('words')} />
        )}
        {Object.entries(books).map(([id, book]) => {
          if (!book.ready) return book.error ? null : <NextSlot key={id} />
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
        {!lessons.hadith.ready && !lessons.hadith.error && <NextSlot />}
        {hadith && (
          <NextStep world={worldOf('hadith')} where={say('{n} of 42', { n: hadith.n })} line={hadith.key.en} onGo={() => onStart('hadith')} />
        )}
        {!lessons.quran.ready && !lessons.quran.error && <NextSlot />}
        {ayah && (
          <NextStep world={worldOf('quran')} where={say('{surah}, ayah {n}', { surah: ayah.name_en, n: ayah.ayah })} line={ayah.english}
            onGo={() => onStart('quran')} />
        )}
      </div>
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

export default function GrowHome({ worlds, rewards, lessons, books, onOpen, onStart, onStartBook }) {
  const statusOf = {
    ...Object.fromEntries(Object.entries(lessons).map(([id, state]) => [id, stageStatus(state)])),
    ...Object.fromEntries(Object.entries(books).map(([id, state]) => [id, bookStatus(state)])),
  }
  const worldOf = (id) => worlds.find((world) => world.id === id)
  return (
    <div className="grow-home">
      <SectionHeader tab="grow" subtitle={say('A little every day, in every part of the app.')}
        aside={rewards ? null : <LogInButton>{say('Log in to keep your XP')}</LogInButton>} />
      <Growth rewards={rewards} />
      <Today worldOf={worldOf} lessons={lessons} books={books} onStart={onStart} onStartBook={onStartBook} />
      <h3 className="grow-worlds-h">{say('Worlds')}</h3>
      <div className="grow-worlds">
        {worlds.map((world, index) => (
          <WorldTile key={world.id} world={world} index={index} {...(statusOf[world.id] ?? {})} onOpen={onOpen} />
        ))}
      </div>
    </div>
  )
}
