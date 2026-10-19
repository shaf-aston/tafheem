import { labelOf } from '../../../lib/tamreen'

import ArabicText from '../../ui/ArabicText'

// An option as shown: the option, and beside it what it points at in the
// picture when it is only a letter ("A", then the sentence A stands for).
export default function OptionText({ part, option }) {
  const label = labelOf(part, option)
  return (
    <>
      <span dir="auto">{option}</span>
      {label && <ArabicText size="sm">{label}</ArabicText>}
    </>
  )
}
