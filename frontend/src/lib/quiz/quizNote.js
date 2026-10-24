/**
 * What has to be said about a quiz question before it is answered: { text, why }
 * or null. `word` is the question on screen, `say` the tab's say().
 *
 * A word that never stands on its own in the Qur'an outranks the dialect: its
 * meaning is not quite a dictionary meaning, and you should know that while you
 * read it, not afterwards. An Urdu speaker meeting a word they already half-know
 * is the one thing this tab can say that nothing else can, so it outranks both.
 * Only ever set on a word a person has checked, and only while the meaning shown
 * is not English: in an English round it answers a question nobody asked.
 */
export function quizNote(word, { language, dialect, say }) {
  const knownInUrdu = language !== 'en' ? word?.urdu : null
  if (knownInUrdu?.kind === 'false-friend') {
    return {
      text: say('not what it looks like'),
      why: say('These letters are an Urdu word too, and there they mean something else: {sense}.',
        { sense: knownInUrdu.sense }),
    }
  }
  if (knownInUrdu) {
    return {
      text: say('you know this one'),
      why: say('These letters are an Urdu word too, and there they mean the same thing.'),
    }
  }
  if (word?.attached) {
    return {
      text: say('from a phrase'),
      // "its meaning", not "its English": in an Urdu round the meaning shown
      // is Urdu, and the old wording said something that was no longer true.
      why: say('This word never stands on its own in the Qur’an, so its meaning '
        + 'is taken from a place where it was attached to another word.'),
    }
  }
  if (dialect) return { text: dialect, why: say('Which Arabic this word is.') }
  return null
}
