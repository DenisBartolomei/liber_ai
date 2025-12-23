import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
      <Toaster 
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#FFF8E7',
            color: '#722F37',
            fontFamily: 'Lato, sans-serif',
          },
          success: {
            iconTheme: {
              primary: '#D4AF37',
              secondary: '#FFF8E7',
            },
          },
          error: {
            iconTheme: {
              primary: '#722F37',
              secondary: '#FFF8E7',
            },
          },
        }}
      />
    </BrowserRouter>
  </React.StrictMode>,
)

