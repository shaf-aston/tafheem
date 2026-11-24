// Copy, numbers and colours in one place, so a client note ("make the counter 999")
// is a one-line change here and never a hunt through the scenes.
// Colours are Tafheem's own tokens (frontend/src/config/theme.json, the Ink look).
export const C = {
  ink: '#0f0d0b',
  bg: '#1b1916',
  glow: '#2c2823',
  surface: 'rgba(35, 32, 28, 0.78)',
  surfaceHi: 'rgba(52, 47, 40, 0.9)',
  border: 'rgba(236, 202, 119, 0.16)',
  borderHi: '#74695a',
  text: '#f2e7d3',
  dim: '#b9ae9b',
  faint: '#8a7f6d',
  gold: '#c9a24b',
  goldHi: '#ecca77',
  paper: '#efe3c6',
  paperText: '#241c11',
  paperMuted: '#6b5c3f',
  paperGold: '#775a15',
  teal: '#5eead4',
  rose: '#fb7185',
  amber: '#fbbf24',
  violet: '#a78bfa',
  violetHi: '#c4b5fd',
  lilac: '#d8b4fe',
  ember: '#f97316',
}

export const FONT = {
  head: "'Fraunces', Georgia, serif",
  label: "'Syne', sans-serif",
  ui: "'Inter', system-ui, sans-serif",
  arabic: "'Noto Naskh Arabic', serif",
  mushaf: "'QPC Hafs', 'Noto Naskh Arabic', serif",
}

export const COPY = {
  hookWord: 'ٱقْرَأْ',
  hookGloss: 'Read.',
  hookRef: "Al-'Alaq 96:1",
  hookQuestion: 'But do you understand what you read?',
  meet: 'Meet',
  name: 'Tafheem',
  nameAr: 'تفهيم',
  problemA: 'Ten tabs open.',
  problemB: 'Still no why.',
  placeholder: 'Type any Arabic sentence…',
  analyse: 'Analyse',
  meaning: 'Indeed, the hard-working student wrote the letter in the big library.',
  demoTitle: 'Every word. Its role. Its rule.',
  demoNote: 'Read by the grammar books’ rules · no AI guessing',
  rootTitle: 'One root. Every word it grows.',
  reciteTitle: 'Recite. Checked word by word.',
  offline: 'Works offline',
  countLabel: 'ayahs, every word with its grammar',
  countSub: '34 classical books  ·  4 dictionaries  ·  every answer cites its source',
  dashTitle: 'Your study',
  closing: 'Now I understand what I read.',
  tagline: 'Read the Qur’an. Understand every word.',
  cta: 'tafheem-app.vercel.app',
  ctaNote: 'Grammar · Roots · Qur’an · Dictionaries · Recitation',
}

// The counter target: change this one number and re-render.
export const COUNT_TO = 6236

// The landing page's demo sentence, with the roles the real analysis gave it
// (frontend/src/landing/assets/demoTree.json). Index 0 is the first word read, on the right.
export const WORDS = [
  { ar: 'إِنَّ', role: 'حَرْفٌ', en: 'particle', gl: 'indeed', tone: C.amber },
  { ar: 'الطَّالِبَ', role: 'اسْمُ إِنَّ', en: 'its noun', gl: 'the student', tone: C.teal },
  { ar: 'الْمُجْتَهِدَ', role: 'صِفَةٌ', en: 'adjective', gl: 'hard-working', tone: C.lilac },
  { ar: 'كَتَبَ', role: 'خَبَرُ إِنَّ', en: 'its news', gl: 'wrote', tone: C.rose },
  { ar: 'الرِّسَالَةَ', role: 'مَفْعُولٌ بِهِ', en: 'object', gl: 'the letter', tone: C.rose },
  { ar: 'فِي', role: 'حَرْفُ جَرٍّ', en: 'preposition', gl: 'in', tone: C.amber },
  { ar: 'الْمَكْتَبَةِ', role: 'مَجْرُورٌ', en: 'governed noun', gl: 'the library', tone: C.teal },
  { ar: 'الْكَبِيرَةِ', role: 'صِفَةٌ', en: 'adjective', gl: 'big', tone: C.lilac },
]

// The joins drawn under the cards, innermost first (from the same demo tree).
export const BRACKETS = [
  { from: 1, to: 2, row: 0, name: 'مُرَكَّبٌ تَوْصِيفِيٌّ', tone: C.violet },
  { from: 6, to: 7, row: 0, name: 'مُرَكَّبٌ تَوْصِيفِيٌّ', tone: C.violet },
  { from: 5, to: 7, row: 1, name: 'جَارٌّ وَمَجْرُورٌ', tone: C.amber },
  { from: 3, to: 7, row: 2, name: 'خَبَرُ إِنَّ', tone: C.rose },
  { from: 0, to: 7, row: 3, name: 'جُمْلَةٌ اسْمِيَّةٌ', tone: C.goldHi },
]

// Root ك ت ب and the words it gives (frontend/src/landing/storyData.js).
export const ROOT_LETTERS = ['ك', 'ت', 'ب']
export const ROOT_WORDS = [
  ['كَتَبَ', 'he wrote', 215],
  ['كِتَاب', 'book', 325],
  ['كَاتِب', 'writer', 180],
  ['مَكْتَب', 'desk, office', 0],
  ['مَكْتُوب', 'written', 145],
  ['مَكْتَبَة', 'library', 35],
]
export const BOOKS = [
  ['Maqayis', 'origin sense'],
  ['Lisan al-Arab', 'full entry'],
  ['Taj al-Arus', 'commentary'],
  ['Lane', 'English'],
]

// Al-'Alaq 96:1, the ayah the recitation check walks through.
export const AYAH = [
  { ar: 'ٱقْرَأْ', gl: 'Read' },
  { ar: 'بِٱسْمِ', gl: 'in the name' },
  { ar: 'رَبِّكَ', gl: 'of your Lord' },
  { ar: 'ٱلَّذِى', gl: 'the One Who' },
  { ar: 'خَلَقَ', gl: 'created' },
]

// The mess in the problem scene: what studying one sentence looks like today.
export const PILE = [
  { title: 'Lisan al-Arab — vol. 1', body: 'ك ت ب : الكِتابُ مَعْروف، والجمع كُتُبٌ…', x: -560, y: -250, r: -7 },
  { title: 'grammar-notes-FINAL(3).pdf', body: 'Inna and her sisters: the noun after it is…?', x: 470, y: -230, r: 6 },
  { title: 'Translation', body: '“Indeed the student wrote…” but why is it الطالبَ?', x: -470, y: 170, r: 5 },
  { title: 'Search', body: 'what does إِنَّ do to the next word', x: 520, y: 210, r: -5 },
  { title: "Lane's Lexicon p. 2589", body: 'كَتَبَ, aor. يَكْتُبُ, inf. n. كَتْبٌ and كِتَابَةٌ…', x: -120, y: -330, r: 3 },
  { title: 'Tafsir', body: 'Scroll… scroll… which word is the subject?', x: 90, y: 320, r: -3 },
]

export const TOOLS = [
  ['Nahw', 'نحو', 'Grammar', C.teal],
  ['Sarf', 'صرف', 'Roots & forms', C.violet],
  ["Qur'an", 'قرآن', 'Word by word', C.goldHi],
  ['Dictionary', 'معجم', '4 lexicons', C.amber],
  ['Hadith', 'حديث', 'Chains', C.rose],
  ['Memorise', 'حفظ', 'Recite', C.lilac],
  ['Quiz', 'اختبار', 'Review', C.teal],
  ['Timelines', 'تاريخ', 'Context', C.ember],
]

export const TODAY = [
  ['إعراب', 'إِنَّ الطَّالِبَ الْمُجْتَهِدَ… analysed'],
  ['جذر', 'Root ك ت ب → 6 words'],
  ['تلاوة', "Recited Al-'Alaq 96:1"],
  ['معجم', 'كِتَاب in Lisan al-Arab'],
  ['اختبار', 'Quiz · 12 of 12'],
]
