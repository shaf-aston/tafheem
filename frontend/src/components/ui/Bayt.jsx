/**
 * The two halves of a bayt as two lines on a phone and side by side from 640px (.bayt in styles/text.css).
 * `halves` are nodes, already in reading order; the verse mark never reaches the page (lib/verse).
 */
export default function Bayt({ halves }) {
  return (
    <span className="bayt">
      {halves.map((half, i) => <span key={i} className="bayt-half">{half}</span>)}
    </span>
  )
}
