import SourceBadge from '../ui/feedback/SourceBadge'

/**
 * English a machine made, with the badge that says so. The badge is pushed to
 * the edge the card's own badge sits on, so the two read as one column of
 * sources rather than one label adrift in the middle of the card.
 */
const MachineEnglish = ({ source, wide = false, children }) => (
  // Held to the reading width, unless `wide`: Word by word sets the book beside
  // its English and needs the card's width for the two.
  <div className={`space-y-1.5 ${wide ? '' : 'max-w-[var(--lexicon-reading-w)]'}`}>
    {children}
    <SourceBadge source={source} className="ms-auto flex" />
  </div>
)

export default MachineEnglish
