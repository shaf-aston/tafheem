/** One tap of the placement check: three options, one right. A pick is final; the line after says why. Options in
 *  Arabic letters are set as Arabic, in a row of their own, as the lesson sets them. */
import ArabicText from '../ui/text/ArabicText'

const IN_ARABIC = /[\u0600-\u06FF]/

export default function Tap({ step, index, picked, onPick, copy }) {
  const item = step.items[index]
  const arabic = item.options.every((text) => IN_ARABIC.test(text))
  const marked = (at) => (picked === undefined ? undefined : at === item.right ? 'right' : at === picked ? 'wrong' : undefined)
  return (
    <div className="grow-card">
      <span className="grow-card-tag">{step.tag} · {index + 1}/{step.items.length}</span>
      <h3 className="type-title font-semibold" dir="auto">{item.question}</h3>
      <div className={`grow-options ${arabic ? 'grow-options-ar' : ''}`} role="radiogroup" aria-label={item.question}>
        {item.options.map((text, at) => (
          <button key={text} type="button" role="radio" aria-checked={at === picked} disabled={picked !== undefined}
            className="grow-option" data-mark={marked(at)} onClick={() => onPick(at)}>
            {arabic ? <ArabicText>{text}</ArabicText> : <span>{text}</span>}
          </button>
        ))}
      </div>
      {picked !== undefined && (
        <p role="status" className="grow-teach-note rise-in">
          <b>{picked === item.right ? copy.right : copy['not-quite']}</b> {item.after}
        </p>
      )}
    </div>
  )
}
