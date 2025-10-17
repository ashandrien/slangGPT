import React from 'react'
import Chat from './components/Chat'

export default function App() {
  return (
    <div className="app-root">
      <header className="app-header">
        <h1>phillygpt</h1>
        <p className="subtitle">philly-slang assistant</p>
      </header>

      <main className="app-main">
        <Chat />
      </main>

      <footer className="app-footer">
        <small>Made with love in Fishtown by <a href="https://github.com/ashandrien">Ash Andrien</a></small>
        <small>Want to support me?  Buy my album on <a href="https://dripcastles.bandcamp.com">Bandcamp</a> (it's $5)</small>
      </footer>
    </div>
  )
}
