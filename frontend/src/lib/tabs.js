/**
 * The tab registry: the one list of what this app is made of.
 *
 * Everything that needs to know the tabs reads this file: the strip under the
 * header, All sections, the command bar, the orbit launcher, the URL. Adding a tab is one
 * entry here; nothing else is edited.
 *
 * Each panel is fetched the first time it opens (React lazy), so the first
 * load carries the shell and not all thirteen tabs.
 */
import { lazy } from 'react'

import { colorFor } from '../theme'
import { colloquialQuery, dawahQuery, daleelBooksQuery, growPathsQuery, hadithOpen, timelinesQuery } from '../api'
import { load } from './warm'
import { memoriseOpen } from './books'
import { table } from './quizBanks'

const Dictionary = lazy(() => import('../components/Dictionary'))
const QuizPanel = lazy(() => import('../components/QuizPanel'))
const QuranLookup = lazy(() => import('../components/QuranLookup'))
const MemorisePanel = lazy(() => import('../components/MemorisePanel'))
const SarfPanel = lazy(() => import('../components/SarfPanel'))
const NahwPanel = lazy(() => import('../components/NahwPanel'))
const DaleelPanel = lazy(() => import('../components/DaleelPanel'))
const HadithPanel = lazy(() => import('../components/HadithPanel'))
const TimelinesPanel = lazy(() => import('../components/TimelinesPanel'))
const DawahPanel = lazy(() => import('../components/DawahPanel'))
const ColloquialPanel = lazy(() => import('../components/ColloquialPanel'))
const GrowPanel = lazy(() => import('../components/GrowPanel'))
const KitPanel = lazy(() => import('../components/KitPanel'))

// `study`: read closely, so the text-size setting applies.
// `half`: two tabs share one slot. Nahw + Sarf: shortest labels, used together.
// `group`: its heading in All sections, an id from GROUPS.
// `mark`: one Arabic letter for where only a letter fits (search rail, launcher
//   ring). Taken from the tab's own name, unique across tabs.
// `open`: fetches the tab's opening data, run on idle and on hovering its tab.
// `hidden`: reachable by URL only (journey and the panel mapping read TABS), left out of
//   everything a person browses; those read LISTED.
// Order = All sections order; the strip is FIXED then RECENT, below. Related tabs sit together.
export const GROUPS = [
  { id: 'language', label: 'Language' },
  { id: 'quran',    label: 'Quran' },
  { id: 'tools',    label: 'Tools' },
]

export const TABS = [
  { id: 'nahw',   label: 'Nahw',       short: 'Nahw',   arabic: 'نحو',    mark: 'ن', Component: NahwPanel,   study: true, half: true, group: 'language' },
  { id: 'sarf',   label: 'Sarf',       short: 'Sarf',   arabic: 'صرف',    mark: 'ص', Component: SarfPanel,   study: true, half: true, group: 'language' },
  { id: 'quran',  label: 'Quran',      short: 'Quran',  arabic: 'القرآن', mark: 'ق', Component: QuranLookup, study: true, dock: true, group: 'quran' },
  // Daleel finds a passage, Dictionary a word: reached for together.
  { id: 'daleel', label: 'Daleel',     short: 'Daleel', arabic: 'دليل',   mark: 'د', Component: DaleelPanel, open: load(daleelBooksQuery), study: true, group: 'quran' },
  { id: 'hadith', label: 'Hadith',     short: 'Hadith', arabic: 'الحديث', mark: 'ث', Component: HadithPanel, open: hadithOpen, study: true, group: 'quran' },
  { id: 'dict',   label: 'Dictionary', short: 'Dict',   arabic: 'قاموس',  mark: 'م', Component: Dictionary,  dock: true, group: 'tools' },
  { id: 'mem',    label: 'Memorise',   short: 'Mem',    arabic: 'حفظ',    mark: 'ح', Component: MemorisePanel, open: memoriseOpen, study: true, group: 'quran' },
  // Grow, نبات (3:37): a learning path, reciting what is said in prayer.
  { id: 'grow',   label: 'Grow!',      short: 'Grow',   arabic: 'نبات',   mark: 'ب', Component: GrowPanel, open: load(growPathsQuery), study: true, dock: true, group: 'quran' },
  { id: 'quiz',   label: 'Quiz',       short: 'Quiz',   arabic: 'اختبار', mark: 'خ', Component: QuizPanel, open: table, dock: true, group: 'tools' },
  { id: 'timelines', label: 'Timelines', short: 'Time', arabic: 'التاريخ', mark: 'ت', Component: TimelinesPanel, open: load(timelinesQuery), study: true, group: 'tools' },
  { id: 'dawah',  label: 'Dawah',      short: 'Dawah',  arabic: 'دعوة',   mark: 'و', Component: DawahPanel, open: load(dawahQuery), study: true, group: 'tools' },
  { id: 'colloq', label: 'Colloquial', short: 'Colloq', arabic: 'عامية',  mark: 'ع', Component: ColloquialPanel, open: load(colloquialQuery), group: 'language', study: true },
  { id: 'kit',    label: 'Kit',        short: 'Kit',    arabic: 'عدة',    mark: 'ك', Component: KitPanel, hidden: true, group: 'tools' },
]

/** The tabs a person can browse to: strip, All sections, command bar, launcher, number keys. */
export const LISTED = TABS.filter((tab) => !tab.hidden)

// The strip: FIXED always shows, in this order, phones too. RECENT follows from
// md: how many, and what they are before anything is opened, oldest first;
// opening another tab drops the oldest (lib/recent.js).
export const FIXED = ['quran', 'nahw', 'sarf', 'dict']
export const RECENT = ['daleel', 'mem', 'quiz', 'grow']

/** A tab's colour, with the theme's own fallback rule. */
export const accentOf = (id) => colorFor('tab', id)
