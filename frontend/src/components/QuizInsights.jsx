/**
 * What the answers add up to: which kinds of word keep going wrong.
 *
 * Shut by default and last on the page, because the quiz is the page. It
 * answers a question a learner only asks between rounds, and a dashboard
 * standing above the question would make a study tool feel like a report card.
 *
 * Everything shown is a count of real answers. No score, no grade, no streak
 * dressed up as a level: the useful sentence is "you keep missing everyday
 * verbs", and everything here exists to reach one of those.
 *
 * Shut, it is still worth reading. A faint line saying "How you're doing" named
 * a subject and promised nothing, so it cost a click to find out whether the
 * click was worth it, and it mostly stayed closed. Now the three figures that
 * answer the question are on the bar itself and the bar is the button: glance,
 * know, carry on, and open it only for what you keep missing.
 *
 * The figures are coloured by what they are, not by how well you are doing:
 * teal for answers that stuck, rose for the pile still owed, plain text for the
 * bare count of answers. A percentage that turned from red to green as it rose
 * would be a grade, which this panel refuses to give; a fixed colour per column
 * is a label, and it is what makes the three legible in one glance.
 */
import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'

import { byCategory, hardestWords, joinStats, overall, slowestWords } from '../lib/insights'
import { fetchSummary } from '../lib/progress'
import { sayIn } from '../lib/say'
import { allWords, groupsFor, moduleFor, QUIZ } from '../lib/quizBanks'

import ArabicText from './ui/ArabicText'
import Disclosure from './ui/Disclosure'
import EmptyState from './ui/EmptyState'
import { Skeleton } from './ui/Skeleton'

// What to call a category on screen. The cuts name themselves in the word
// list, so only these few are named here: the sets, and the types of word.
const NAMES = {
  book: 'Qur’an, the 80% list',
  quran: 'Qur’an, all of it',
  everyday: 'Everyday speech',
  noun: 'Nouns',
  verb: 'Verbs',
  adjective: 'Adjectives',
  particle: 'Particles',
}

const percent = (fraction) => `${Math.round(fraction * 100)}%`
const seconds = (ms) => `${(ms / 1000).toFixed(1)}s`

export default function QuizInsights({ accent, language }) {
  const say = sayIn(language)
  // Re-read whenever an answer has been filed. It used to be keyed to the round
  // instead, on the argument that renumbering mid-round would distract; that was
  // written when this was a shut drawer with a faint label on it. Now the three
  // figures are on the bar and always in view, and a figure in view that is not
  // the truth is worse than a figure that moves. The panel does not ask for
  // itself: QuizPanel invalidates 'quiz-progress' once an answer is saved, so
  // the reading follows the store and never the other way round.
  const stats = useQuery({
    // Keyed by language as well: each language is counted under its own module,
    // so the figures on the bar are the ones for the round being played.
    queryKey: ['quiz-progress', language],
    queryFn: () => fetchSummary(moduleFor(language)),
    staleTime: Infinity,
    refetchOnWindowFocus: false,
  })
  const words = useQuery({ queryKey: ['quiz-words', 'all'], queryFn: allWords, staleTime: Infinity })
  const groups = useQuery({ queryKey: ['quiz-groups', 'quranic'], queryFn: () => groupsFor('quranic'), staleTime: Infinity })

  // Joined and totalled once per round, not once per render: the bar reads the
  // same numbers the opened panel does, so the two can never disagree, and a
  // reopen re-uses the answer instead of walking every row again.
  const joined = useMemo(
    () => (stats.data && words.data ? joinStats(stats.data, words.data) : null),
    [stats.data, words.data],
  )
  const totals = useMemo(
    () => (joined?.rows.length ? overall(joined.rows) : null),
    [joined],
  )

  return (
    <Disclosure
      framed
      bodyClassName="px-4 pt-1 pb-4"
      label={<StatBar totals={totals} say={say} />}
    >
      <Body joined={joined} stats={stats} words={words} groups={groups} accent={accent}
        say={say} language={language} />
    </Disclosure>
  )
}

/**
 * The three figures on the shut bar: how much stuck, how much was answered,
 * how much is still owed. Chosen because they are the three a learner between
 * rounds actually asks for, and because each is a plain count that cannot be
 * argued with.
 *
 * Nothing is shown before the counts are in. A figure that appears as a zero
 * and then jumps once the answers load would have told you something untrue in
 * the meantime, and this bar's whole job is being readable without opening it.
 */
function StatBar({ totals, say }) {
  if (!totals || totals.accuracy === null) return <>{say('How you’re doing, all time')}</>

  return (
    <span className="flex items-center justify-between gap-3 min-w-0">
      <span className="flex items-baseline gap-5 sm:gap-8 min-w-0">
        <Figure value={percent(totals.accuracy)} name={say('right')} tone="var(--success)" />
        <Figure value={totals.attempts} name={say('answered')} />
        {totals.inReview > 0 && (
          <Figure value={totals.inReview} name={say('to review')} tone="var(--danger)" />
        )}
      </span>
      <span className="type-small text-[var(--text-faint)] shrink-0 hidden sm:inline">
        {say('What you keep missing')}
      </span>
    </span>
  )
}

// Number above its name rather than beside it: stacked, the eye reads three
// figures across the bar and only drops to the labels if it needs them.
function Figure({ value, name, tone }) {
  return (
    <span className="flex flex-col gap-0.5 min-w-0">
      <span
        className="type-figure font-semibold tabular-nums"
        style={{ color: tone ?? 'var(--text)' }}
      >
        {value}
      </span>
      <span className="type-small uppercase tracking-wide text-[var(--text-faint)] truncate">
        {name}
      </span>
    </span>
  )
}

function Body({ joined, stats, words, groups, accent, say, language }) {
  if (stats.isPending || words.isPending) return <Skeleton className="h-24 w-full" />

  // A reading nobody can make is said plainly rather than drawn as zeroes,
  // which would read as "you have got everything right".
  if (stats.isError) {
    return (
      <p className="type-small text-[var(--text-faint)]">
        {say('Your answers can’t be read right now, so there is nothing to show yet.')}
      </p>
    )
  }

  const { rows, orphans } = joined ?? { rows: [], orphans: [] }
  if (!rows.length && !orphans.length) {
    return <EmptyState>{say('Answer a few questions and what you keep missing will show up here.')}</EmptyState>
  }

  // The set and word-type names are interface; a surah's own name is content
  // and stays as the word list wrote it.
  const labels = Object.fromEntries(Object.entries(NAMES).map(([key, name]) => [key, say(name)]))
  for (const section of groups.data ?? []) {
    for (const option of section.options) labels[option.id] = option.label
  }

  const totals = overall(rows)
  const categories = byCategory(rows, { minAttempts: QUIZ.insightMinAttempts, labels }).slice(0, 5)
  const hardest = hardestWords(rows)
  const slowest = slowestWords(rows, 3)

  return (
    <div className="space-y-4">
      {/* The percentage and the count are on the bar above, so what is left to
          say here is the part the bar has no room for: how many words those
          answers covered. */}
      <p className="type-body text-[var(--text-dim)]">
        {say(totals.words === 1 ? 'Across {n} word.' : 'Across {n} words.', { n: totals.words })}
        {totals.inReview > 0 && (
          <> {say('{n} still waiting in Mistakes.', { n: totals.inReview })}</>
        )}
      </p>

      {categories.length > 0 && (
        <Group title={say('What you miss most')}>
          <div className="flex flex-wrap gap-1.5">
            {categories.map((category) => (
              <span
                key={category.key}
                title={say('{wrong} wrong out of {attempts}', category)}
                style={{ borderColor: accent }}
                className="type-small leading-none px-2.5 py-1.5 rounded-full
                  border bg-[var(--surface)] text-[var(--text-dim)]"
              >
                {category.label}
                <span className="text-[var(--text-faint)] tabular-nums">
                  {' · '}{say('{wrong}/{attempts} wrong', category)}
                </span>
              </span>
            ))}
          </div>
        </Group>
      )}

      {/* The two word lists side by side once there is room. Each row is a
          short word, a short gloss and a count, so full width left a hand's
          width of nothing down the middle of both. They stack again below the
          breakpoint, where one column is all there is. */}
      <div className="grid gap-4 sm:grid-cols-2 sm:gap-x-10">
        {hardest.length > 0 && (
          <Group title={say('Words you get wrong most')}>
            <WordRows rows={hardest} language={language}
              count={(row) => say('{wrong}/{attempts} wrong', row)} />
          </Group>
        )}

        {slowest.length > 0 && (
          <Group title={say('Words you take longest on')}>
            <WordRows rows={slowest} language={language} count={(row) => seconds(row.avgMs)} />
          </Group>
        )}
      </div>

      {/* Said, not swallowed. A word answered before the word list was last
          built has a record and nothing to attach it to; hiding those rows
          would quietly change every count above them. */}
      {orphans.length > 0 && (
        <p className="type-tiny text-[var(--text-faint)]">
          {say(
            orphans.length === 1
              ? '{n} answered word is no longer in the word list, so it is left out above.'
              : '{n} answered words are no longer in the word list, so they are left out above.',
            { n: orphans.length },
          )}
        </p>
      )}
    </div>
  )
}

/**
 * A word, its meaning, and one number about it.
 *
 * Both lists are this shape and only differ in what the number counts, so the
 * two columns cannot drift into two slightly different rows. In a column the
 * gloss is the part that has to give, hence the truncation on it and not on the
 * word or the count.
 */
function WordRows({ rows, count, language }) {
  return (
    <ul className="space-y-1">
      {rows.map((row) => (
        <li key={row.item} className="flex items-baseline justify-between gap-3">
          <ArabicText size="sm">{row.word.ar}</ArabicText>
          {/* The meaning in the language the round was played in. A word with
              none falls back to its English rather than showing an empty row. */}
          {language !== 'en' && row.word[language] ? (
            <ArabicText lang={language} size="sm" className="text-[var(--text-dim)] flex-1 truncate">
              {row.word[language]}
            </ArabicText>
          ) : (
            <span className="type-body text-[var(--text-dim)] flex-1 truncate" title={row.word.en}>
              {row.word.en}
            </span>
          )}
          <span className="type-small text-[var(--text-faint)] tabular-nums shrink-0">
            {count(row)}
          </span>
        </li>
      ))}
    </ul>
  )
}

function Group({ title, children }) {
  return (
    <div className="space-y-1.5">
      <h3 className="type-small uppercase tracking-wide text-[var(--text-faint)]">{title}</h3>
      {children}
    </div>
  )
}
