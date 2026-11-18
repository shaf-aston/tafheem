// A topic's words split into the ones it teaches new and the ones an earlier topic taught (`met`,
// marked by the loader from the course order), so no word is taught as new twice. A list from an
// older payload (no `met` on its words) is all new, as before.
export const splitMet = (words) => [words.filter((w) => !w.met), words.filter((w) => w.met)]
