/**
 * The tab registry: the one list of what this app is made of.
 *
 * Everything that needs to know the tabs reads this file: the strip under the
 * header, the command bar, the orbit launcher, the URL. Adding a tab is one
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

// `study` marks the panels that are read closely rather than glanced at, the
// text the size setting moves. The rest keep one size.
// `half` puts two tabs in the space of one. Nahw and Sarf are the two shortest
// words on the strip and the two that are always reached for together, so they
// share a block and leave a whole one for Memorise rather than squeezing all
// eight evenly and shortening every label.
//
// Pairing more tabs was tried for the seventh and made it worse: "Dictionary"
// is a long word and half a block cannot hold it. What the seventh tab needed
// was not narrower tabs but fewer things inside each one, so the Arabic name
// now waits for a wider screen (see TabStrip). Timelines is the eighth and the
// last the strip can hold; the ninth needs the menu, not a narrower tab.
//
// `mark` is the one Arabic letter that stands for the tab where there is only
// room for a letter: the rail beside a search result, a satellite in the
// launcher. Each is taken from the tab's own Arabic name and each is different
// from the other six, which first letters alone are not: القرآن and اختبار both
// start with ا, and two identical chips in different colours is a puzzle, not
// a shortcut.
export const TABS = [
  { id: 'nahw',  label: 'Nahw',       short: 'Nahw',   arabic: 'نحو',    mark: 'ن', Component: NahwPanel,   study: true, half: true },
  { id: 'sarf',  label: 'Sarf',       short: 'Sarf',   arabic: 'صرف',    mark: 'ص', Component: SarfPanel,   study: true, half: true },
  { id: 'quran', label: 'Quran',      short: 'Quran',  arabic: 'القرآن', mark: 'ق', Component: QuranLookup, study: true },
  // Daleel sits next to the Qur'an because it is the tab that finds a passage
  // rather than studying one already found; the two are reached for together.
  { id: 'daleel', label: 'Daleel',    short: 'Daleel', arabic: 'دليل',   mark: 'د', Component: DaleelPanel, study: true },
  { id: 'mem',   label: 'Memorise',   short: 'Mem',    arabic: 'حفظ',    mark: 'ح', Component: MemorisePanel, study: true },
  { id: 'dict',  label: 'Dictionary', short: 'Dict',   arabic: 'قاموس',  mark: 'م', Component: Dictionary },
  { id: 'quiz',  label: 'Quiz',       short: 'Quiz',   arabic: 'اختبار', mark: 'خ', Component: QuizPanel },
  // The eighth tab, and the one that says the strip has reached its limit: past
  // this, tabs move into a menu rather than getting narrower (see TabStrip).
  { id: 'timelines', label: 'Timelines', short: 'Time', arabic: 'التاريخ', mark: 'ت', Component: TimelinesPanel, study: true },
]

/** A tab's colour, with the theme's own fallback rule. */
export const accentOf = (id) => colorFor('tab', id)
