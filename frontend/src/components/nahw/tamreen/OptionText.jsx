import { labelOf } from '../../../lib/nahw/tamreen'

import ArabicText from '../../ui/text/ArabicText'

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
