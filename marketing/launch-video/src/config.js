// Copy, numbers and colours in one place, so a client note ("make the counter 999")
// is a one-line change here and never a hunt through the shots.
// The look follows the reference launch video (warm brown glow, glass cards, one hot
// accent plus lavender); the accent is saffron, a nod to Tafheem's gold.
export const C = {
  black: '#060302',
  base: '#1a0a04',
  ember: '#5c2209',
  emberHi: '#8a3510',
  card: 'rgba(18, 11, 8, 0.86)',
  cardHi: 'rgba(30, 19, 13, 0.9)',
  line: 'rgba(255, 236, 220, 0.09)',
  glassFill: 'rgba(120, 70, 45, 0.28)',
  glassLine: 'rgba(255, 226, 204, 0.55)',
  text: '#fbf4ee',
  dim: '#c9b8ab',
  faint: '#8f7f74',
  saffron: '#f4913b',
  saffronHi: '#ffb867',
  peach: '#f6c48c',
  lavender: '#8d95e6',
  navy: '#1d2564',
  cream: '#f2ebe6',
  paper: '#ebe5e3',
  ink: '#1d1a19',
  green: '#1f3b2e',
}

export const FONT = {
  ui: "'Inter', 'Noto Naskh Arabic', system-ui, sans-serif",
  arabic: "'Noto Naskh Arabic', serif",
  mushaf: "'QPC Hafs', 'Noto Naskh Arabic', serif",
  mono: "'Code Mono', monospace",
}

export const COPY = {
  question: 'Do you understand what you recite?',
  meet: 'Meet',
  name: 'Tafheem',
  hello: 'Salaam',
  bot: 'Salaam! I’m here to help you understand every word',
  user: 'Explain this ayah to me, word by word',
  prompt: 'Break down every word of this ayah',
  connect: 'Connect the classical books',
  connecting: 'Connecting 34 books',
  counting: 'Counting every word',
  countLabel: 'ayahs, word by word',
  dash: 'Dashboard',
  final: 'Now I understand what I read. Let’s keep going',
  finalHint: ['Suggestions', 'Explain إِنَّ and her sisters', 'Quiz me on root ك ت ب', 'Read Al-ʿAlaq next'],
  url: 'tafheem-app.vercel.app',
}

// The counter target: change this one number and re-render.
export const COUNT_TO = 6236

// The analysis that scrolls past in the stream shot: Al-ʿAlaq 96:1 word by word,
// the way the app's Nahw and Sarf tools report it.
export const STREAM = [
  ['{', ''],
  ['  "ayah": "96:1",', ''],
  ['  "word": "', 'ٱقْرَأْ', '",'],
  ['  "type": "fi‘l amr · imperative verb",', ''],
  ['  "root": "', 'ق ر أ', '",'],
  ['  "i‘rab": "', 'مَبْنِيٌّ عَلَى السُّكُونِ', '",'],
  ['  "subject": "hidden pronoun · you",', ''],
  ['},', ''],
  ['{', ''],
  ['  "word": "', 'بِٱسْمِ', '",'],
  ['  "type": "harf jarr + ism majrur",', ''],
  ['  "root": "', 'س م و', '",'],
  ['  "i‘rab": "', 'جَارٌّ وَمَجْرُورٌ', '",'],
  ['},', ''],
  ['{', ''],
  ['  "word": "', 'رَبِّكَ', '",'],
  ['  "type": "mudaf ilayh · genitive",', ''],
  ['  "root": "', 'ر ب ب', '",'],
  ['  "sources": ["Lisan al-Arab", "Lane", "Maqayis"]', ''],
  ['},', ''],
  ['{', ''],
  ['  "word": "', 'خَلَقَ', '",'],
  ['  "type": "fi‘l madi · past verb",', ''],
  ['  "root": "', 'خ ل ق', '",'],
  ['  "form": "I · fa‘ala",', ''],
  ['}', ''],
]

// The three tool cards (shot 9 and the dashboard). Glyph is the icon letter.
export const CARDS = [
  { glyph: 'ن', eyebrow: 'GRAMMAR · NAHW', title: 'Analyse every word', sub: 'I‘rab, roles & sentence tree', note: '34 books' },
  { glyph: 'ص', eyebrow: 'MORPHOLOGY · SARF', title: 'Trace every root', sub: 'Forms, patterns & word family', note: '4 lexicons' },
  { glyph: 'ق', eyebrow: 'QUR’AN', title: 'Read word by word', sub: 'Recitation, meaning & tafsir', note: '6,236 ayahs' },
]

// The app's eight tools, in its own tab order, with the tile colour each gets.
export const TOOLS = [
  ['Nahw', 'نحو', 'saffron'],
  ['Sarf', 'صرف', 'cream'],
  ['Qur’an', 'قرآن', 'peach'],
  ['Daleel', 'دليل', 'saffron'],
  ['Memorise', 'حفظ', 'lavender'],
  ['Dictionary', 'قاموس', 'navy'],
  ['Quiz', 'اختبار', 'ink'],
  ['Timelines', 'تاريخ', 'cream'],
]

export const LESSONS = [
  ['ٱقْرَأْ analysed', 'now'],
  ['Root ق ر أ traced', '2 s'],
  ['Al-ʿAlaq 96:1 recited', '5 s'],
  ['كِتَاب in Lane’s Lexicon', '9 s'],
  ['Quiz · 12 of 12', '14 s'],
  ['Timeline · Cave of Hira', '20 s'],
]

// Demo figures on the dashboard (like the reference's "999"): change freely.
export const DASH = { wordsToday: 16, wordsUp: '+4', streak: 40, tools: '8 of 8' }
