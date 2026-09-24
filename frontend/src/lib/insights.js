/**
 * Reading a record of answers as "what do I keep getting wrong".
 *
 * Pure functions, like quiz.js beside it: answers and words in, findings out,
 * no fetching and no clock. That is what makes the reading testable without a
 * server, and what keeps the store on the other side of it ignorant of Arabic.
 *
 * The store files an answer under a meaningKey and nothing else. Everything a
 * category is made of, whether a word is a noun or a verb, whether it belongs
 * to a topic in the book or to everyday speech, is already on the word in
 * words.json, so the join happens here, where that table is already loaded.
 * Copying those tags into the database instead would make a second copy that
 * goes stale the next time the word list is built.
 *
 * A rate is only shown once enough answers stand behind it. Two wrong out of
 * two is not a weakness, it is a Tuesday, and a panel that calls it one sends
 * somebody off to study a category they have barely met.
 */

/**
 * Put each item's record beside the word it refers to.
 *
 * Synonyms share a meaningKey, so several words can answer to one record. The
 * first is kept, because the record is of the meaning rather than the spelling.
 *
 * Anything with no word left in the list comes back separately rather than
 * being dropped: a word that was answered and has since left the build is a
 * fact about the data worth showing, not a row to swallow quietly.
 */
export function joinStats(items, words) {
  const byKey = new Map()
  for (const word of words) {
    if (!byKey.has(word.meaningKey)) byKey.set(word.meaningKey, word)
  }

  const rows = []
  const orphans = []
  for (const stat of items) {
    const word = byKey.get(stat.item)
    if (word) rows.push({ ...stat, word })
    else orphans.push(stat)
  }
  return { rows, orphans }
}

/**
 * The groups one word belongs to, as categories.
 *
 * A tag reads `set:topic`, `everyday:travel` or `book:v-naqis`, so it names two
 * things at once: which list the word came from and which group inside it. Both
 * are worth knowing, "you miss everyday words" and "you miss hollow verbs" are
 * different findings, so both are counted.
 */
function categoriesOf(word) {
  const found = [{ kind: 'type', key: word.wordType }]
  for (const tag of word.groups ?? []) {
    const [set, topic] = tag.split(':')
    found.push({ kind: 'set', key: set })
    if (topic) found.push({ kind: 'topic', key: tag })
  }
  return found.filter((category) => category.key)
}

/**
 * Which kinds of word are going wrong most, worst first.
 *
 * `labels` names a category in the words the app already uses for it; a key
 * with no entry keeps its own name rather than being hidden.
 */
export function byCategory(rows, { minAttempts = 1, labels = {} } = {}) {
  const buckets = new Map()

  for (const row of rows) {
    for (const { kind, key } of categoriesOf(row.word)) {
      const bucket = buckets.get(key) ?? { key, kind, label: labels[key] ?? key, attempts: 0, wrong: 0 }
      bucket.attempts += row.attempts
      bucket.wrong += row.wrong
      buckets.set(key, bucket)
    }
  }

  return [...buckets.values()]
    .filter((bucket) => bucket.attempts >= minAttempts && bucket.wrong > 0)
    .map((bucket) => ({ ...bucket, rate: bucket.wrong / bucket.attempts }))
    .sort((a, b) => b.rate - a.rate || b.wrong - a.wrong)
}

/** The individual words got wrong most often, worst first. */
export function hardestWords(rows, count = 5) {
  return rows
    .filter((row) => row.wrong > 0)
    .sort((a, b) => b.wrong - a.wrong || b.wrong / b.attempts - a.wrong / a.attempts)
    .slice(0, count)
}

/**
 * The words that take longest to answer, slowest first.
 *
 * Only words with a timing the store was willing to average: one left open
 * while somebody made tea says nothing about how well the word is known.
 */
export function slowestWords(rows, count = 5) {
  return rows
    .filter((row) => row.avgMs != null)
    .sort((a, b) => b.avgMs - a.avgMs)
    .slice(0, count)
}

/** The one line at the top: how much has been answered, and how much of it stuck. */
export function overall(rows) {
  const attempts = rows.reduce((total, row) => total + row.attempts, 0)
  const wrong = rows.reduce((total, row) => total + row.wrong, 0)
  return {
    attempts,
    wrong,
    words: rows.length,
    accuracy: attempts ? (attempts - wrong) / attempts : null,
    inReview: rows.filter((row) => row.inReview).length,
  }
}
