/**
 * Put each one in its group (fard / sunnah / mustahabb, and the like). `value` maps an item's index to the group picked.
 * Once checked, a row put in the wrong group is marked, so the learner sees which ones slipped.
 */
import { sayIn } from '../../../lib/text/say'

const say = sayIn('en')

export default function SortCard({ card, value, setValue, result }) {
  const chosen = value ?? {}
  const markOf = (item, i, group) => {
    if (!result) return chosen[i] === group ? 'picked' : undefined
    if (item.into === group) return 'right'
    return chosen[i] === group ? 'wrong' : undefined
  }
  return (
    <div className="grow-card">
      <span className="grow-card-tag">{say(card.tag)}</span>
      <p className="grow-card-ask grow-ask-strong">{card.ask}</p>
      <ul className="grow-sort">
        {card.items.map((item, i) => (
          <li key={item.text} className="grow-sort-row" data-miss={result && chosen[i] !== item.into ? '' : undefined}>
            <span className="grow-sort-text">{item.text}</span>
            <span className="grow-sort-groups" role="radiogroup" aria-label={item.text}>
              {card.into.map((group) => (
                <button key={group} type="button" role="radio" aria-checked={chosen[i] === group} className="grow-option grow-sort-pick"
                  data-mark={markOf(item, i, group)} disabled={Boolean(result)} onClick={() => setValue({ ...chosen, [i]: group })}>
                  {group}
                </button>
              ))}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
