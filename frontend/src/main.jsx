import React from 'react'
import { createRoot } from 'react-dom/client'

import App from './App'
import { GraphProvider } from './state/GraphContext'
import './styles.css'

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <GraphProvider>
      <App />
    </GraphProvider>
  </React.StrictMode>
)
