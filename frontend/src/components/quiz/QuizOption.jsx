/**
 * One answer to pick, numbered, its verdict riding on its border once answered.
 * The Quiz board's options and the Colloquial tab's choose exercise both draw
 * this, so a pick looks and moves the same wherever it is asked.
 *
 * `option` is { id, text }; `answerId` and `picked` are option ids; `say`
 * words the verdict in the round's language.
 */
import ArabicText from '../ui/ArabicText'

export default function QuizOption({ option, index, lang, say, answered, picked, answerId, accent, onChoose }) {
  const isAnswer = option.id === answerId
  const isPicked = option.id === picked

  // Before answering the accent guides; after, only right and wrong matter.
  let border = 'var(--border)'
  let color = 'var(--text)'
  if (answered && isAnswer) {
    border = 'var(--success)'
    color = 'var(--success)'
  } else if (answered && isPicked) {
    border = 'var(--danger)'
    color = 'var(--danger)'
  }

  // The verdict rides on the option itself. That keeps the answer and the word
  // it belongs to in one place, and saves a whole row below the grid. It sits
  // on the border, taking no room from the text: inside the row, a long
  // meaning wrapped to make space for it and the option grew as it arrived.
  let verdict = null
  if (answered && isAnswer) verdict = say(isPicked ? 'Correct' : 'Answer')
  else if (answered && isPicked) verdict = say('Not this')

  return (
    <button
      type="button"
      onClick={() => onChoose(option.id)}
      disabled={answered}
      style={{ '--i': index, '--c': accent, borderColor: border, color }}
      className={`rise-in option relative flex items-center gap-3 px-4 py-3 rounded-[var(--radius-md)] text-start
        bg-[var(--surface-hi)] border
        ${answered ? 'cursor-default' : ''}
        ${answered && !isAnswer && !isPicked ? 'opacity-50' : ''}`}
    >
      <span
        className="shrink-0 w-6 h-6 grid place-items-center rounded-full type-small
          bg-[var(--surface)] text-[var(--text-faint)]"
        aria-hidden="true"
      >
        {index + 1}
      </span>
      {lang === 'en' ? (
        <span className="text-sm">{option.text}</span>
      ) : (
        <ArabicText lang={lang} className="leading-tight">{option.text}</ArabicText>
      )}
      {verdict && (
        <span className="absolute -top-2.5 end-3 px-1.5 rounded type-tiny font-medium leading-5 bg-[var(--surface)]">
          {verdict}
        </span>
      )}
    </button>
  )
}
