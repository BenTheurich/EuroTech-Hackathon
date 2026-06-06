import './App.css'
import { useLocationSocket } from './useLocationSocket'
import { useSmoothedLocation } from './useSmoothedLocation'
import MapView from './MapView'

const STATUS_LABELS = {
  connecting: 'Connecting…',
  connected: 'Live',
  disconnected: 'Reconnecting…',
}

function App() {
  const { status, targetPosition } = useLocationSocket()
  const { position, trail } = useSmoothedLocation(targetPosition)

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>Indoor Positioning</h1>
          <p className="subtitle">Live Wi-Fi fingerprint tracking</p>
        </div>
        <div className={`status status-${status}`}>
          <span className="status-dot" />
          {STATUS_LABELS[status] || status}
        </div>
      </header>

      <main className="map-wrap">
        <MapView position={position} trail={trail} />
      </main>

      <footer className="app-footer">
        {position ? (
          <span>
            Position: x = {position.x.toFixed(1)}, y = {position.y.toFixed(1)}
            {' '}
            confidence = {Math.round((position.confidence ?? 1) * 100)}%
          </span>
        ) : (
          <span>Waiting for the first reading from the scanner…</span>
        )}
      </footer>
    </div>
  )
}

export default App
