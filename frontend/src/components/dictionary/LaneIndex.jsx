import { useId, useState } from 'react'

import config from '../../config/dictionary.json'
import { foldForSearch } from '../../lib/text/arabicText'

import Chip from '../ui/inputs/Chip'
import ShowRest from '../ui/buttons/ShowRest'

/**
 * Every headword in the entry, one press from its section. Lane on a common
 * root runs to thousands of words; this is how a reader finds the one they came
 * for without reading down to it. Right to left, like the words themselves.
 *
 * Three rows show; typing in the box narrows the chips to the words that hold
 * what was typed, harakat or none, and shows every one that does. The old
 * "All words" press opened all forty at once, which was the wall again.
 *
 * `rail`: a wide screen sets the index beside the entry, held in view as the
 * entry scrolls, every word shown and the list scrolling on its own.
 */
export default function LaneIndex({ forms, onJump, accent, rail = false }) {
  const [find, setFind] = useState('')
  const id = useId()
  const wanted = foldForSearch(find).trim()
  const words = forms.map((form, i) => ({ form, i }))
    .filter(({ form }) => form.word && (!wanted || foldForSearch(form.word).includes(wanted)))
  const chips = (
    <nav dir="rtl" aria-label="Words in this entry" className="flex flex-wrap gap-1.5">
      {words.map(({ form, i }) => (
        <Chip key={i} arabic accent={accent} onClick={() => onJump(i)}
          title={form.form ? `Form ${form.form}` : undefined}>
          {form.word}
        </Chip>
      ))}
    </nav>
  )

  const findable = forms.filter((form) => form.word).length >= config.lane['find-from']
  if (!findable && !rail) return chips

  return (
    <div className={rail ? 'space-y-2 lg:sticky lg:top-[calc(var(--app-header-h,0px)+1rem)]' : 'space-y-2'}>
      {findable && <>
      {/* A small filter, not the page's search box: it narrows a list already
          on screen, and a box the size of the dictionary's own read as a
          second search. dir=auto turns it round at the first Arabic letter. */}
      <input id={id} type="search" dir="auto" value={find} onChange={(event) => setFind(event.target.value)}
        placeholder="Find a word" aria-label="Find a word in this entry" style={{ '--c': accent }}
        className="w-full max-w-60 rounded-full border border-[var(--border-hi)] bg-[var(--surface)] px-3 py-1.5
          type-ui text-[var(--text)] placeholder:text-[var(--text-faint)] focus:border-[var(--c)] focus:outline-none" />
      </>}
      {wanted && !words.length && <p className="type-small text-[var(--text-faint)]">No word here holds {find}.</p>}
      {rail ? <div className="max-h-[70vh] overflow-y-auto overscroll-contain pe-1">{chips}</div>
        : wanted ? chips : <ShowRest lines={3} accent={accent} more="All words">{chips}</ShowRest>}
    </div>
  )
}
