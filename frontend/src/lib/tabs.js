/**
 * The tab registry: the one list of what this app is made of.
 *
 * Everything that needs to know the tabs reads this file: the strip under the
 * header, All sections, the command bar, the orbit launcher, the URL. Adding a tab is one
 * entry here; nothing else is edited.
 *
 * Each panel's code is its own file (lib/panel.js), so the first load carries the
 * shell and not all fourteen tabs. The code is fetched with the tab's opening
 * data (App.jsx openTab: idle, hover), so a tab opens at once and still opens
 * after the network drops.
 */
import { colorFor } from '../theme'
import { colloquialQuery, dawahQuery, daleelBooksQuery, hadithOpen, timelinesQuery } from '../api'
import { load } from './warm'
import { memoriseOpen } from './books'
import { table } from './quizBanks'
import { WORDS_MODULE } from './wordPractice'
import { MODULE as HADITH_MODULE } from './hadithLesson'
import { MODULE as QURAN_MODULE } from './quranLesson'
import { panel } from './panel'
import grow from '../worlds.json'
import { quranOpen } from './quranOpen'

const HomePanel = panel(() => import('../components/home/HomePanel'))
const Dictionary = panel(() => import('../components/Dictionary'))
const QuizPanel = panel(() => import('../components/QuizPanel'))
const QuranLookup = panel(() => import('../components/QuranLookup'))
const MemorisePanel = panel(() => import('../components/MemorisePanel'))
const SarfPanel = panel(() => import('../components/SarfPanel'))
const NahwPanel = panel(() => import('../components/NahwPanel'))
const DaleelPanel = panel(() => import('../components/DaleelPanel'))
const HadithPanel = panel(() => import('../components/HadithPanel'))
const TimelinesPanel = panel(() => import('../components/TimelinesPanel'))
const DawahPanel = panel(() => import('../components/DawahPanel'))
const ColloquialPanel = panel(() => import('../components/ColloquialPanel'))
const GrowPanel = panel(() => import('../components/GrowPanel'))
const KitPanel = panel(() => import('../components/KitPanel'))

// `study`: read closely, so the text-size setting applies.
// `half`: two tabs share one slot. Nahw + Sarf: shortest labels, used together.
// `group`: its heading in All sections, an id from GROUPS.
// `blurb`: one plain line on what you do there (Home's cards).
// `mark`: one Arabic letter for where only a letter fits (search rail, launcher
//   ring). Taken from the tab's own name, unique across tabs.
// `open`: fetches the tab's opening data, run on idle and on hovering its tab.
// `modules`: other names its answers are filed under in the progress store, so a
//   progress row can say which tab it came from.
// `hidden`: reachable by URL only (journey and the panel mapping read TABS), left out of
//   everything a person browses; those read LISTED.
// Home is first, so it is where a visit with no saved place opens.
// Order = All sections order; the strip is FIXED then RECENT, below. Related tabs sit together.
export const GROUPS = [
  { id: 'start',    label: 'Start' },
  { id: 'language', label: 'Language' },
  { id: 'quran',    label: 'Quran' },
  { id: 'tools',    label: 'Tools' },
]

// What Grow files its answers under: the hadith and Qur'an worlds' own names, and
// each book world's `module` as worlds.json declares it, so a new book needs no edit here.
const GROW_MODULES = [HADITH_MODULE, QURAN_MODULE, ...grow.worlds.filter((world) => world.module).map((world) => world.module)]

export const TABS = [
  { id: 'home',   label: 'Home',       short: 'Home',   arabic: 'البداية', mark: 'ه', Component: HomePanel, blurb: "Where you left off, your progress, and every tab", group: 'start' },
  { id: 'nahw',   label: 'Nahw',       short: 'Nahw',   arabic: 'نحو',    mark: 'ن', Component: NahwPanel,   study: true, half: true, blurb: "Type a sentence: every word's role and the reason", group: 'language' },
  { id: 'sarf',   label: 'Sarf',       short: 'Sarf',   arabic: 'صرف',    mark: 'ص', Component: SarfPanel,   study: true, half: true, blurb: "Conjugate any root, or read a verb back", group: 'language' },
  { id: 'quran',  label: 'Quran',      short: 'Quran',  arabic: 'القرآن', mark: 'ق', Component: QuranLookup, open: quranOpen, study: true, blurb: "Read, search and study the Qur'an word by word", group: 'quran' },
  // Daleel finds a passage, Dictionary a word: reached for together.
  { id: 'daleel', label: 'Daleel',     short: 'Daleel', arabic: 'دليل',   mark: 'د', Component: DaleelPanel, open: load(daleelBooksQuery), study: true, blurb: "Find the passage that speaks to your question", group: 'quran' },
  { id: 'hadith', label: 'Hadith',     short: 'Hadith', arabic: 'الحديث', mark: 'ح', Component: HadithPanel, open: hadithOpen, study: true, blurb: "Search hadith, with narrators and grading", group: 'quran' },
  { id: 'dict',   label: 'Dictionary', short: 'Dict',   arabic: 'قاموس',  mark: 'م', Component: Dictionary,  study: true, blurb: "Look up an Arabic word, root or meaning", group: 'tools' },
  { id: 'mem',    label: 'Memorise',   short: 'Mem',    arabic: 'حفظ',    mark: 'ف', Component: MemorisePanel, open: memoriseOpen, study: true, blurb: "Learn verses by heart and check your recital", group: 'quran' },
  // Grow, نبات (3:37): a little every day: words, fiqh, Quran and hadith.
  { id: 'grow',   label: 'Grow!',      short: 'Grow',   arabic: 'نبات',   mark: 'ب', Component: GrowPanel, study: true, blurb: "A little every day: words, fiqh, Quran and hadith", group: 'quran', modules: GROW_MODULES },
  { id: 'quiz',   label: 'Quiz',       short: 'Quiz',   arabic: 'اختبار', mark: 'خ', Component: QuizPanel, open: table, blurb: "Practise words and meanings, and review what is due", group: 'tools' },
  { id: 'timelines', label: 'Timelines', short: 'Time', arabic: 'التاريخ', mark: 'ت', Component: TimelinesPanel, open: load(timelinesQuery), study: true, blurb: "See events and their ayat laid out in order", group: 'tools' },
  { id: 'dawah',  label: 'Dawah',      short: 'Dawah',  arabic: 'دعوة',   mark: 'و', Component: DawahPanel, open: load(dawahQuery), study: true, blurb: "Answers to common questions, with the evidence", group: 'tools' },
  { id: 'colloq', label: 'Colloquial', short: 'Colloq', arabic: 'عامية',  mark: 'ع', Component: ColloquialPanel, open: load(colloquialQuery), blurb: "Everyday spoken Arabic, by dialect", group: 'language', study: true, modules: [WORDS_MODULE] },
  { id: 'kit',    label: 'Kit',        short: 'Kit',    arabic: 'عدة',    mark: 'ك', Component: KitPanel, hidden: true, blurb: "Small tools for study", group: 'tools' },
]

/** The tabs a person can browse to: strip, All sections, command bar, launcher, number keys. */
export const LISTED = TABS.filter((tab) => !tab.hidden)

// The strip: FIXED always shows, in this order, phones too. RECENT follows from
// md: eight slots in all, so Home joining FIXED cost RECENT one; how many, and
// what they are before anything is opened, oldest first;
// opening another tab drops the oldest (lib/recent.js).
export const FIXED = ['home', 'quran', 'nahw', 'sarf', 'dict']

/** The tab the app opens on, and the group of All sections that holds only it. */
export const HOME = FIXED[0]
export const START = GROUPS[0].id
export const RECENT = ['daleel', 'mem', 'quiz']

// The phone's bar until the reader changes it (lib/dock.js): these, in this order, then More.
export const DOCK = ['home', 'quran', 'dict', 'quiz']

/** A tab's colour, with the theme's own fallback rule. */
export const accentOf = (id) => colorFor('tab', id)
