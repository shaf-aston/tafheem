/**
 * The tab registry: the one list of what this app is made of.
 *
 * Everything that needs to know the tabs reads this file: the strip under the
 * header, All sections, the command bar, the orbit launcher, the URL. Adding a tab is one
 * entry here; nothing else is edited.
 */
import { colorFor } from '../theme'
import { colloquialQuery, dawahQuery, daleelBooksQuery, growPathsQuery, hadithOpen, timelinesQuery } from '../api'
import { load } from './warm'
import { memoriseOpen } from './books'
import { table } from './quizBanks'

import Dictionary from '../components/Dictionary'
import QuizPanel from '../components/QuizPanel'
import QuranLookup from '../components/QuranLookup'
import MemorisePanel from '../components/MemorisePanel'
import SarfPanel from '../components/SarfPanel'
import NahwPanel from '../components/NahwPanel'
import DaleelPanel from '../components/DaleelPanel'
import HadithPanel from '../components/HadithPanel'
import TimelinesPanel from '../components/TimelinesPanel'
import DawahPanel from '../components/DawahPanel'
import ColloquialPanel from '../components/ColloquialPanel'
import GrowPanel from '../components/GrowPanel'

// `study`: read closely, so the text-size setting applies.
// `half`: two tabs share one slot. Nahw + Sarf: shortest labels, used together,
//   so opening one brings the other out beside it.
// `row`: when the tab shows in the strip. 1 always, 2 from md, 3 only through
//   a recent tab (RECENT below; the strip is capped at the page width, so it never grows).
//   Every tab is always in All sections (SectionsMenu); tier 1 is what a phone fits.
// `group`: its heading in All sections, an id from GROUPS.
// `mark`: one Arabic letter for where only a letter fits (search rail, launcher
//   ring). Taken from the tab's own name, unique across tabs.
// `open`: fetches the tab's opening data, run on idle and on hovering its tab.
// Order = strip order = number-key shortcuts. Related tabs sit together.
export const GROUPS = [
  { id: 'language', label: 'Language' },
  { id: 'quran',    label: 'Quran' },
  { id: 'tools',    label: 'Tools' },
]

export const TABS = [
  { id: 'nahw',   label: 'Nahw',       short: 'Nahw',   arabic: 'نحو',    mark: 'ن', Component: NahwPanel,   study: true, half: true, row: 3, group: 'language' },
  { id: 'sarf',   label: 'Sarf',       short: 'Sarf',   arabic: 'صرف',    mark: 'ص', Component: SarfPanel,   study: true, half: true, row: 3, group: 'language' },
  { id: 'quran',  label: 'Quran',      short: 'Quran',  arabic: 'القرآن', mark: 'ق', Component: QuranLookup, study: true, dock: true, row: 1, group: 'quran' },
  // Daleel finds a passage, Dictionary a word: reached for together.
  { id: 'daleel', label: 'Daleel',     short: 'Daleel', arabic: 'دليل',   mark: 'د', Component: DaleelPanel, open: load(daleelBooksQuery), study: true, row: 1, group: 'quran' },
  { id: 'hadith', label: 'Hadith',     short: 'Hadith', arabic: 'الحديث', mark: 'ث', Component: HadithPanel, open: hadithOpen, study: true, row: 3, group: 'quran' },
  { id: 'dict',   label: 'Dictionary', short: 'Dict',   arabic: 'قاموس',  mark: 'م', Component: Dictionary,  dock: true, row: 1, group: 'tools' },
  { id: 'mem',    label: 'Memorise',   short: 'Mem',    arabic: 'حفظ',    mark: 'ح', Component: MemorisePanel, open: memoriseOpen, study: true, row: 2, group: 'quran' },
  // Grow, نبات (3:37): a learning path, reciting what is said in prayer.
  { id: 'grow',   label: 'Grow!',      short: 'Grow',   arabic: 'نبات',   mark: 'ب', Component: GrowPanel, open: load(growPathsQuery), study: true, dock: true, row: 3, group: 'quran' },
  { id: 'quiz',   label: 'Quiz',       short: 'Quiz',   arabic: 'اختبار', mark: 'خ', Component: QuizPanel, open: table, dock: true, row: 2, group: 'tools' },
  { id: 'timelines', label: 'Timelines', short: 'Time', arabic: 'التاريخ', mark: 'ت', Component: TimelinesPanel, open: load(timelinesQuery), study: true, row: 3, group: 'tools' },
  { id: 'dawah',  label: 'Dawah',      short: 'Dawah',  arabic: 'دعوة',   mark: 'و', Component: DawahPanel, open: load(dawahQuery), study: true, row: 3, group: 'tools' },
  { id: 'colloq', label: 'Colloquial', short: 'Colloq', arabic: 'عامية',  mark: 'ع', Component: ColloquialPanel, open: load(colloquialQuery), row: 3, group: 'language', study: true },
]

// The recent tabs at the strip's far right: how many, and what they are before
// anything is opened, oldest first. Opening a row 3 tab drops the oldest
// (lib/recent.js).
export const RECENT = ['hadith', 'grow']

/** A tab's colour, with the theme's own fallback rule. */
export const accentOf = (id) => colorFor('tab', id)
