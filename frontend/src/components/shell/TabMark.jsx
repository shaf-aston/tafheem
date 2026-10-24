/**
 * A tab's picture where only a small mark fits: the phone's bar, the dock editor, the
 * search rail and rows, the launcher ring. The tab's own Emblem, held still and drawn in
 * the text colour around it, so a lit tab lights its picture too (styles/emblem.css).
 */
import Emblem from '../ui/Emblem'

export default function TabMark({ tab }) {
  return tab ? <Emblem id={tab.emblem} className="tab-mark" /> : null
}
