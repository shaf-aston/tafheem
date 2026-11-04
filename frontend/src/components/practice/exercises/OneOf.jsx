/**
 * One answer from a few, numbered: 1-4 on the keyboard picks it (lib/quiz/useAnswerKeys, as in the Quiz), and once
 * checked the right one and the reader's wrong pick are marked. Short answers sit two by two when they pair up evenly
 * (three would leave one alone); long English ones keep a row each.
 */
import ArabicText from '../../ui/text/ArabicText'
import OptionNumber from '../../ui/inputs/OptionNumber'
import { useAnswerKeys } from '../../../lib/quiz/useAnswerKeys'

// About one line of a half-width option at body size.
const SHORT = 24

export default function OneOf({ options, answer, value, setValue, result, arabic = false, label }) {
  useAnswerKeys({ checked: Boolean(result), optionCount: options.length }, {
    toggle: (event, index) => setValue(options[index].id),
  })
  const markOf = (option) => {
    if (!result) return option.id === value ? 'picked' : undefined
    if (option.id === answer) return 'right'
    return option.id === value ? 'wrong' : undefined
  }
  const two = options.length % 2 === 0 && (arabic || options.every((option) => option.text.length <= SHORT))
  return (
    <div className={['grow-options', arabic && 'grow-options-ar', two && 'grow-options-two'].filter(Boolean).join(' ')} role="radiogroup" aria-label={label}>
      {options.map((option, i) => (
        <button key={option.id} type="button" role="radio" aria-checked={option.id === value} className="grow-option"
          data-mark={markOf(option)} disabled={Boolean(result)} onClick={() => setValue(option.id)}>
          <OptionNumber index={i} />
          {arabic ? <ArabicText>{option.text}</ArabicText> : <span>{option.text}</span>}
        </button>
      ))}
    </div>
  )
}
