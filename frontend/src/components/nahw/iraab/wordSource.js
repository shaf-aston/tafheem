// The word a word takes its case from: its عامل, or the word a تابع follows.
export const source = (w) => w.governor ?? w.follows ?? undefined
