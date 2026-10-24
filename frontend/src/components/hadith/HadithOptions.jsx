import { useHideChain } from '../../lib/hadith/useHideChain'
import { useSideBySide } from '../../lib/hadith/useSideBySide'

import ReadingOptions from '../ui/ReadingOptions'

/**
 * The reading options for a list that has no bar of its own (search hits, Starred), so
 * the chain can be hidden wherever hadiths are read, not only inside a book.
 */
export default function HadithOptions({ accent }) {
  const [sideBySide, setSideBySide] = useSideBySide()
  const [hideChain, setHideChain] = useHideChain()
  return (
    <div className="flex flex-wrap items-center justify-end gap-2">
      <ReadingOptions accent={accent} options={[
        { label: 'Side by side', on: sideBySide, set: setSideBySide, only: 'wide' },
        { label: 'Hide the chain', on: hideChain, set: setHideChain },
      ]} />
    </div>
  )
}
