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
