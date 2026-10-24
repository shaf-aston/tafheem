/**
 * The tab registry: the one list of what this app is made of.
 *
 * Everything that needs to know the tabs reads this file: the strip under the
 * header, All sections, the command bar, the orbit launcher, the URL. Adding a tab is one
 * entry here; nothing else is edited.
 *
 * Each panel's code is its own file (lib/panel.js), so the first load carries the
 * shell and not every tab. The code is fetched with the tab's opening
 * data (App.jsx openTab: idle, hover), so a tab opens at once and still opens
 * after the network drops.
 */
import { colorFor } from '../theme'
import { colloquialQuery, dawahQuery, daleelBooksQuery, hadithOpen, timelinesQuery } from '../api'
import { load } from './warm'
import { memoriseOpen } from './books'
import { table } from './quizBanks'
import { WORDS_MODULE } from './colloquial/wordPractice'
import { MODULE as BASICS_MODULE } from './alifLam'
import { MODULE as HADITH_MODULE } from './hadithLesson'
import { MODULE as QURAN_MODULE } from './quranLesson'
import { panel } from './panel'
import grow from '../config/worlds.json'
import { quranOpen } from './quranOpen'
import { similarOpen } from './similarOpen'

const HomePanel = panel(() => import('../components/home/HomePanel'))
const DictionaryPanel = panel(() => import('../components/dictionary/DictionaryPanel'))
const QuizPanel = panel(() => import('../components/quiz/QuizPanel'))
const QuranPanel = panel(() => import('../components/quran/QuranPanel'))
const MemorisePanel = panel(() => import('../components/memorise/MemorisePanel'))
const SimilarPanel = panel(() => import('../components/similar/SimilarPanel'))
const SarfPanel = panel(() => import('../components/sarf/SarfPanel'))
const NahwPanel = panel(() => import('../components/nahw/NahwPanel'))
const DaleelPanel = panel(() => import('../components/daleel/DaleelPanel'))
const HadithPanel = panel(() => import('../components/hadith/HadithPanel'))
const TimelinesPanel = panel(() => import('../components/timelines/TimelinesPanel'))
const DawahPanel = panel(() => import('../components/dawah/DawahPanel'))
const ColloquialPanel = panel(() => import('../components/colloquial/ColloquialPanel'))
const GrowPanel = panel(() => import('../components/grow/GrowPanel'))
const KitPanel = panel(() => import('../components/kit/KitPanel'))

// `study`: read closely, so the text-size setting applies.
// `half`: two tabs share one slot. Nahw + Sarf: shortest labels, used together.
// `group`: its heading in All sections, an id from GROUPS.
// `blurb`: one plain line on what you do there (Home's cards).
// `emblem`: the tab's picture (components/ui/Emblem.jsx), on its title and wherever
//   only a small mark fits (phone bar, search rail, launcher ring). Unique across tabs.
// `open`: fetches the tab's opening data, run on idle and on hovering its tab.
// `modules`: other names its answers are filed under in the progress store, so a
//   progress row can say which tab it came from.
// `ownsHealth`: draws its own offline state, so the app-wide backend banner stays off it.
// `hidden`: reachable by URL only (journey and the panel mapping read TABS), left out of
//   everything a person browses; those read LISTED.
// Home is first, so it is where a visit with no saved place opens.
// Order = All sections order; the strip is FIXED then RECENT, below. Related tabs sit together.
// Grouped by what you came to do, one word each, so a choice is a goal, then a tab.
export const GROUPS = [
  { id: 'start',    label: 'Start' },
  { id: 'read',     label: 'Read' },
  { id: 'arabic',   label: 'Understand' },
  { id: 'practise', label: 'Practise' },
  { id: 'more',     label: 'Explore' },
]

// What Grow files its answers under: the Basics, hadith and Qur'an worlds' own names, and
// each book world's `module` as worlds.json declares it, so a new book needs no edit here.
const GROW_MODULES = [BASICS_MODULE, HADITH_MODULE, QURAN_MODULE, ...grow.worlds.filter((world) => world.module).map((world) => world.module)]

export const TABS = [
  { id: 'home',   label: 'Home',       short: 'Home',   arabic: 'البداية', emblem: 'home', Component: HomePanel, ownsHealth: true, blurb: "Where you left off, your progress, and every tab", group: 'start' },
  { id: 'nahw',   label: 'Nahw',       short: 'Nahw',   arabic: 'نحو',    emblem: 'nahw', Component: NahwPanel,   study: true, half: true, blurb: "Type a sentence: every word's role and the reason", group: 'arabic' },
  { id: 'sarf',   label: 'Sarf',       short: 'Sarf',   arabic: 'صرف',    emblem: 'sarf', Component: SarfPanel,   study: true, half: true, blurb: "Conjugate any root, or read a verb back", group: 'arabic' },
  { id: 'quran',  label: 'Quran',      short: 'Quran',  arabic: 'القرآن', emblem: 'quran', Component: QuranPanel, open: quranOpen, study: true, blurb: "Read, search and study the Qur'an word by word", group: 'read' },
  // Daleel finds a passage, Dictionary a word: reached for together.
  { id: 'daleel', label: 'Daleel',     short: 'Daleel', arabic: 'دليل',   emblem: 'daleel', Component: DaleelPanel, open: load(daleelBooksQuery), study: true, blurb: "Find the passage that speaks to your question", group: 'read' },
  { id: 'hadith', label: 'Hadith',     short: 'Hadith', arabic: 'الحديث', emblem: 'hadith', Component: HadithPanel, open: hadithOpen, study: true, blurb: "Search hadith, with narrators and grading", group: 'read' },
  { id: 'dict',   label: 'Dictionary', short: 'Dict',   arabic: 'قاموس',  emblem: 'dict', Component: DictionaryPanel, study: true, blurb: "Look up an Arabic word, root or meaning", group: 'arabic' },
  { id: 'mem',    label: 'Memorise',   short: 'Mem',    arabic: 'حفظ',    emblem: 'mem', Component: MemorisePanel, open: memoriseOpen, study: true, blurb: "Learn verses by heart and check your recital", group: 'practise' },
  // Similar verses, متشابهات: telling look-alike ayat apart, next to learning them by heart.
  { id: 'similar', label: 'Similar',        short: 'Similar', arabic: 'متشابهات', emblem: 'similar', Component: SimilarPanel, open: similarOpen, study: true, blurb: "Tell look-alike verses apart, and drill the wording", group: 'practise' },
  // Grow, نبات (3:37): a little every day: words, fiqh, Quran and hadith.
  { id: 'grow',   label: 'Grow!',      short: 'Grow',   arabic: 'نبات',   emblem: 'words', Component: GrowPanel, study: true, blurb: "A little every day: words, fiqh, Quran and hadith", group: 'practise', modules: GROW_MODULES },
  { id: 'quiz',   label: 'Quiz',       short: 'Quiz',   arabic: 'اختبار', emblem: 'quiz', Component: QuizPanel, open: table, blurb: "Practise words and meanings, and review what is due", group: 'practise' },
  { id: 'timelines', label: 'Timelines', short: 'Time', arabic: 'التاريخ', emblem: 'timelines', Component: TimelinesPanel, open: load(timelinesQuery), study: true, blurb: "See events and their ayat laid out in order", group: 'more' },
  { id: 'dawah',  label: 'Dawah',      short: 'Dawah',  arabic: 'دعوة',   emblem: 'dawah', Component: DawahPanel, open: load(dawahQuery), study: true, blurb: "Answers to common questions, with the evidence", group: 'more' },
  { id: 'colloq', label: 'Colloquial', short: 'Colloq', arabic: 'عامية',  emblem: 'colloq', Component: ColloquialPanel, open: load(colloquialQuery), blurb: "Spoken, everyday Arabic dialects", group: 'arabic', study: true, modules: [WORDS_MODULE] },
  { id: 'kit',    label: 'Kit',        short: 'Kit',    arabic: 'عدة',    emblem: 'kit', Component: KitPanel, hidden: true, blurb: "Small tools for study", group: 'more' },
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
