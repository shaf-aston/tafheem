/**
 * The tab registry: the one list of what this app is made of.
 *
 * Everything that needs to know the tabs reads this file: the strip under the
 * header, All sections, the command bar, the orbit launcher, the URL. Adding a tab is one
 * entry here; nothing else is edited.
 */
import { colorFor } from '../theme'

import Dictionary from '../components/Dictionary'
import QuizPanel from '../components/QuizPanel'
import QuranLookup from '../components/QuranLookup'
import MemorisePanel from '../components/MemorisePanel'
import SarfPanel from '../components/SarfPanel'
import NahwPanel from '../components/NahwPanel'
import DaleelPanel from '../components/DaleelPanel'
import TimelinesPanel from '../components/TimelinesPanel'
import ColloquialPanel from '../components/ColloquialPanel'

// `study`: read closely, so the text-size setting applies.
// `half`: two tabs share one slot. Nahw + Sarf: shortest labels, used together.
// `row`: when the tab shows in the strip. 1 always, 2 from md, 3 never
//   (the strip is capped at the page width, so wider screens gain no room).
//   Every tab is always in All sections (SectionsMenu); tier 1 is what a phone fits.
// `group`: its heading in All sections, an id from GROUPS.
// `mark`: one Arabic letter for where only a letter fits (search rail, launcher
//   ring). Taken from the tab's own name, unique across tabs.
// Order = strip order = number-key shortcuts. Related tabs sit together.
export const GROUPS = [
  { id: 'language', label: 'Language' },
  { id: 'quran',    label: 'Quran' },
  { id: 'tools',    label: 'Tools' },
]

export const TABS = [
  { id: 'nahw',   label: 'Nahw',       short: 'Nahw',   arabic: 'نحو',    mark: 'ن', Component: NahwPanel,   study: true, half: true, row: 1, group: 'language' },
  { id: 'sarf',   label: 'Sarf',       short: 'Sarf',   arabic: 'صرف',    mark: 'ص', Component: SarfPanel,   study: true, half: true, row: 1, group: 'language' },
  { id: 'quran',  label: 'Quran',      short: 'Quran',  arabic: 'القرآن', mark: 'ق', Component: QuranLookup, study: true, row: 1, group: 'quran' },
  // Daleel finds a passage, Dictionary a word: reached for together.
  { id: 'daleel', label: 'Daleel',     short: 'Daleel', arabic: 'دليل',   mark: 'د', Component: DaleelPanel, study: true, row: 1, group: 'quran' },
  { id: 'dict',   label: 'Dictionary', short: 'Dict',   arabic: 'قاموس',  mark: 'م', Component: Dictionary,  row: 1, group: 'tools' },
  { id: 'mem',    label: 'Memorise',   short: 'Mem',    arabic: 'حفظ',    mark: 'ح', Component: MemorisePanel, study: true, row: 2, group: 'quran' },
  { id: 'quiz',   label: 'Quiz',       short: 'Quiz',   arabic: 'اختبار', mark: 'خ', Component: QuizPanel,   row: 2, group: 'tools' },
  { id: 'timelines', label: 'Timelines', short: 'Time', arabic: 'التاريخ', mark: 'ت', Component: TimelinesPanel, study: true, row: 3, group: 'tools' },
  { id: 'colloq', label: 'Colloquial', short: 'Colloq', arabic: 'عامية',  mark: 'ع', Component: ColloquialPanel, row: 3, group: 'language' },
]

/** A tab's colour, with the theme's own fallback rule. */
export const accentOf = (id) => colorFor('tab', id)
