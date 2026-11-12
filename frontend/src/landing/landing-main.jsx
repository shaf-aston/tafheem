// Every page loads the one shared sheet, so a component the landing borrows
// from the app (MicMark) arrives with its styles.
import '../styles/index.css'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import { applyTheme } from '../theme'
import theme from '../config/theme.json'
import Landing from './Landing.jsx'

applyTheme()

// The landing is the dark look. A first visit that goes on into the app lands in that same look, not in
// whatever the device prefers, so "See it in action" opens the page it promised. Only when the app has never
// been opened here (no hint yet): a look already chosen, or Device already followed, is left alone.
// The app then starts from this hint until the reader picks a look in Settings (lib/store/settings.js).
document.addEventListener('click', (event) => {
  const link = event.target.closest?.('a[href]')
  if (!link || new URL(link.href, location.href).origin !== location.origin || link.pathname === location.pathname) return
  // Straight to storage: lib/store/stored would bring the learner's progress code into the landing's bundle.
  try {
    if (!localStorage.getItem(theme.themes['hint-key'])) localStorage.setItem(theme.themes['hint-key'], theme.themes.base)
  } catch { /* private browsing: the app follows the device, as before */ }
})

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Landing />
  </StrictMode>,
)
