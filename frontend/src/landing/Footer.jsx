import FooterNote from '../components/shell/FooterNote.jsx'

export default function Footer() {
  return (
    <footer className="legal">
      {/* The landing is one long read; the note at its foot is the same as the app's. */}
      <FooterNote where="landing" accent="var(--gold)" />
      <p className="legal-line">Built on references</p>
    </footer>
  )
}
