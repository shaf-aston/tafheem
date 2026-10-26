import './notfound.css'

import links from '../landing/links.json'

// The path the visitor actually hit, shown so a mistyped or stale link is
// obvious at a glance instead of a guessing game.
function currentPath() {
  if (typeof window === 'undefined') return ''
  return window.location.pathname + window.location.search
}

export default function NotFound() {
  return (
    <main className="landing-page notfound-page">
      <div className="wrap">
        <p className="eyebrow label">Tafheem</p>
        <p className="notfound-digits" aria-hidden="true">404</p>
        <h1 className="headline">This page doesn&rsquo;t exist.</h1>
        <p className="notfound-copy">
          The address may be mistyped, the page may have moved, or it was never
          part of the site.
        </p>
        <div className="cta-row">
          <a href={links.tool} className="cta">Open the tool</a>
          <a href="/" className="cta ghost">Back to the start</a>
        </div>
        <p className="notfound-path">{currentPath()}</p>
      </div>
    </main>
  )
}
