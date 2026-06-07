import { Link } from 'react-router-dom'
import '../../App.css'
import { useLocationSocket } from '../../useLocationSocket'
import { useSmoothedLocation } from '../../useSmoothedLocation'
import MapView from '../../MapView'

const STATUS_LABELS = {
  connecting: 'Connecting…',
  connected: 'Live',
  disconnected: 'Reconnecting…',
}

// The backend's LocationTracker tags every estimate with how it was derived, so
// the strip below can show the physics-aware tracker working in real time.
const TRACKER_STATUS = {
  live: { label: 'Live', cls: 'ts-live' },
  held: { label: 'Holding still', cls: 'ts-held' },
  smoothed: { label: 'Smoothed', cls: 'ts-smoothed' },
  constrained: { label: 'Speed-limited', cls: 'ts-constrained' },
  low_confidence: { label: 'Low confidence', cls: 'ts-low' },
}

function Metric({ label, value, title, warn = false }) {
  return (
    <span className={`metric ${warn ? 'metric-warn' : ''}`} title={title}>
      <span className="metric-label">{label}</span>
      <span className="metric-value">{value}</span>
    </span>
  )
}

function TrackerBadge({ status }) {
  const ts = TRACKER_STATUS[status] || TRACKER_STATUS.live
  return (
    <span className="metric">
      <span className="metric-label">Tracker</span>
      <span className={`ts-badge ${ts.cls}`}>
        <span className="ts-dot" />
        {ts.label}
      </span>
    </span>
  )
}

// Full-screen user-facing tracking view. Driven by the backend KNN websocket
// (useLocationSocket) and smoothed for display (useSmoothedLocation).
export default function LiveMap() {
  const { status, targetPosition } = useLocationSocket()
  const { position, trail } = useSmoothedLocation(targetPosition)

  return (
    <div className="app live-map-page">
      <header className="app-header">
        <div>
          <h1>RmFindr</h1>
          <p className="subtitle">
            <Link to="/" className="app-backlink">← Admin dashboard</Link>
            {' · '}Live Wi-Fi fingerprint tracking
          </p>
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
          <div className="telemetry">
            <span className="telemetry-legend">
              <span className="swatch swatch-user" /> Tracked
              <span className="swatch swatch-raw" /> Raw KNN
            </span>
            <Metric
              label="Position"
              value={`${position.x.toFixed(1)}, ${position.y.toFixed(1)} m`}
            />
            <TrackerBadge status={position.trackerStatus} />
            <Metric
              label="Confidence"
              value={`${Math.round((position.confidence ?? 1) * 100)}%`}
            />
            <Metric
              label="Match"
              title="KNN fingerprint distance to the nearest calibrated point — lower is a closer match"
              value={
                position.nearestDistance != null
                  ? `Δ${position.nearestDistance.toFixed(1)}`
                  : '—'
              }
            />
            <Metric
              label="Signal age"
              title="How long ago the underlying Wi-Fi scan was taken"
              value={position.scanAgeMs != null ? `${position.scanAgeMs} ms` : '—'}
            />
            <Metric
              label="Anchors"
              title="Anchors that dropped out this scan and were carried forward from a recent reading"
              warn={position.carried?.length > 0}
              value={
                position.carried?.length
                  ? `${position.carried.length} carried`
                  : 'all live'
              }
            />
          </div>
        ) : (
          <span>Waiting for the first reading from the scanner…</span>
        )}
      </footer>
    </div>
  )
}
