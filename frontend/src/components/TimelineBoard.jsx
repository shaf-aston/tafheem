/**
 * The way into a section: a board of big tinted tiles on the tab's home, and
 * once one is chosen the same tiles shrunk to a row along the top, the chosen
 * one stronger. Pressing the chosen one again goes back to the board.
 *
 * Which picture and hue each section wears is timelines.json's, read through
 * lib/timelineLayout; the card look is ui/TileCard.
 */
import ArabicText from './ui/ArabicText'
import TileCard from './ui/TileCard'
import { sectionLook } from '../lib/timelineLayout'

export default function TimelineBoard({ sections, current = null, onPick }) {
  if (current) {
    return (
      <div className="tl-minis" role="group" aria-label="Timelines">
        {sections.map((section, i) => {
          const { icon, hue } = sectionLook(section.id)
          const on = section.id === current
          return (
            <TileCard
              key={section.id}
              variant="mini"
              hue={hue}
              icon={icon}
              index={i}
              pressed={on}
              label={section.name}
              onClick={() => onPick(on ? null : section.id)}
            >
              <span className="tl-count">{section.events.length}</span>
              <span className="tl-title">{section.name}</span>
              <ArabicText size="sm" className="tl-ar arabic-inline">{section.arabic}</ArabicText>
            </TileCard>
          )
        })}
      </div>
    )
  }

  return (
    <div className="tl-board">
      {sections.map((section, i) => {
        const { icon, hue } = sectionLook(section.id)
        return (
          <TileCard key={section.id} variant="tile" hue={hue} icon={icon} index={i} onClick={() => onPick(section.id)}>
            <span className="tl-chip">{section.events.length} moments</span>
            <h3 className="tl-title">{section.name}</h3>
            <ArabicText className="tl-ar arabic-inline">{section.arabic}</ArabicText>
            <span className="tl-sub">{section.sub}</span>
            {section.kind === 'unseen' && (
              <span className="sr-only">Unseen: known by revelation, not by history.</span>
            )}
          </TileCard>
        )
      })}
    </div>
  )
}
