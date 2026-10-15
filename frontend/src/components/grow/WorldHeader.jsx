/** A world's header: back button, scene, name, idea. Colour from --w. */
import { sayIn } from '../../lib/say'
import ArabicText from '../ui/ArabicText'

const say = sayIn('en')

export default function WorldHeader({ world, onBack, children }) {
  return (
    <header className="grow-world-hd">
      <button type="button" className="grow-back" onClick={onBack} aria-label={say('Back to all worlds')}>
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2"
          strokeLinecap="round" strokeLinejoin="round"><path d="M15 18l-6-6 6-6" /></svg>
        <span>{say('Worlds')}</span>
      </button>
      <div className="grow-world-title">
        <div>
          <p className="grow-world-scene">{world.scene}</p>
          <h2>{world.name}</h2>
          <p className="grow-world-idea">{world.idea}</p>
        </div>
        <ArabicText size="lg" className="grow-world-ar">{world.arabic}</ArabicText>
      </div>
      {children}
    </header>
  )
}
