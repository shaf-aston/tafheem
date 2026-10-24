/** A world's header: back button, scene, name, idea. Colour from --w. `back` names where the button goes (default: all worlds). */
import { sayIn } from '../../lib/text/say'
import Emblem from '../ui/Emblem'
import ArabicText from '../ui/ArabicText'

const say = sayIn('en')

export default function WorldHeader({ world, onBack, back = say('Worlds'), children }) {
  return (
    <header className="grow-world-hd">
      <button type="button" className="grow-back" onClick={onBack} aria-label={say('Back to {where}', { where: back })}>
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2"
          strokeLinecap="round" strokeLinejoin="round"><path d="M15 18l-6-6 6-6" /></svg>
        <span>{back}</span>
      </button>
      <div className="grow-world-title">
        <div>
          <p className="grow-world-scene">{world.scene}</p>
          <h2>{world.name}</h2>
          <p className="grow-world-idea">{world.idea}</p>
        </div>
        <span className="grow-world-pic">
          <Emblem id={world.id} size={64} />
          <ArabicText size="lg" className="grow-world-ar">{world.arabic}</ArabicText>
        </span>
      </div>
      {children}
    </header>
  )
}
