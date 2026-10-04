// Every page loads the one shared sheet, so a component the landing borrows
// from the app (TarkeebDiagram, MicMark) arrives with its styles.
import '../styles/index.css'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import { applyTheme } from '../theme'
import Landing from './Landing.jsx'

applyTheme()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Landing />
  </StrictMode>,
)
