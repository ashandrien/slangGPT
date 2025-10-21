import React from 'react'
import Chat from './components/Chat'

export default function App() {
  return (
    <div className="app-root">
      <header className="app-header">
  <h1>SlangGPT</h1>
  <p className="subtitle">local-slang assistant</p>
      </header>

      <main className="app-main">
        <Chat />
      </main>

      <footer className="app-footer">
        <small>Made with love in Fishtown by <a href="https://github.com/ashandrien">Ash Andrien</a></small><br />
        <small>Want to support me?  Buy my album on <a href="https://dripcastles.bandcamp.com">Bandcamp</a> (it's $5)</small>
        <p><iframe style="border: 0; width: 100%; height: 42px;" src="https://bandcamp.com/EmbeddedPlayer/album=3528796175/size=small/bgcol=ffffff/linkcol=2ebd35/transparent=true/" seamless><a href="https://dripcastles.bandcamp.com/album/dauphin-street-demos">Dauphin Street Demos by Drip Castles</a></iframe></p>
      </footer>
    </div>
  )
}
