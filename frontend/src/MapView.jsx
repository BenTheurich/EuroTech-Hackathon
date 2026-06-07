import { confidenceRingRadius } from './locationSmoothing'

// ============================================================================
// COORDINATE CONTRACT  (the one place to edit when the KNN coordinate space
// is finalized with whoever owns the backend model)
//
// The backend predicts an (x, y) inside FLOOR's bounds. ANCHORS are the known
// hotspot positions in that SAME space. These values match the real
// fingerprints in fingerprints1400.csv: the 7 x 5 m demo room (meters),
// x = 0..7, y = 0..5, anchors in the four corners.
// ============================================================================
const FLOOR = { minX: 0, maxX: 7, minY: 0, maxY: 5 }

const ANCHORS = [
  { id: 'A', label: 'Anchor A', x: 0, y: 0 },
  { id: 'B', label: 'Anchor B', x: 7, y: 0 },
  { id: 'C', label: 'Anchor C', x: 0, y: 5 },
  { id: 'D', label: 'Anchor D', x: 7, y: 5 },
]

const PADDING = 0.45
const ANCHOR_SIZE = 0.34

export default function MapView({ position, trail }) {
  const width = FLOOR.maxX - FLOOR.minX
  const height = FLOOR.maxY - FLOOR.minY
  const viewBox = `${FLOOR.minX - PADDING} ${FLOOR.minY - PADDING} ${
    width + PADDING * 2
  } ${height + PADDING * 2}`

  const trailPoints = trail.map((p) => `${p.x},${p.y}`).join(' ')
  const confidenceRadius = position ? confidenceRingRadius(position.confidence) : 0

  return (
    <svg className="map-svg" viewBox={viewBox} preserveAspectRatio="xMidYMid meet">
      {/* Floor plan area — drop a real floor-plan <image> here later */}
      <rect
        x={FLOOR.minX}
        y={FLOOR.minY}
        width={width}
        height={height}
        className="map-floor"
      />

      {/* Faint grid for spatial reference */}
      <Grid />

      {/* Path the user has walked */}
      {trail.length > 1 && (
        <polyline points={trailPoints} className="map-trail" />
      )}

      {/* Anchor (hotspot) markers */}
      {ANCHORS.map((a) => (
        <g key={a.id} transform={`translate(${a.x}, ${a.y})`}>
          <rect
            x={-ANCHOR_SIZE / 2}
            y={-ANCHOR_SIZE / 2}
            width={ANCHOR_SIZE}
            height={ANCHOR_SIZE}
            rx={0.06}
            className="map-anchor"
          />
          <text className="map-anchor-label" y={0.08} textAnchor="middle" fontSize={0.22}>
            {a.id}
          </text>
        </g>
      ))}

      {/* Live user position */}
      {position && (
        <g
          className={`map-user map-user-${position.trackerStatus || 'live'}`}
          transform={`translate(${position.x}, ${position.y})`}
        >
          <circle
            r={confidenceRadius}
            className="map-user-confidence"
          />
          <circle r={0.32} className="map-user-pulse" />
          <circle r={0.13} className="map-user-dot" />
        </g>
      )}
    </svg>
  )
}

function Grid() {
  const lines = []

  for (let x = FLOOR.minX + 1; x < FLOOR.maxX; x++) {
    lines.push(
      <line key={`v${x}`} x1={x} y1={FLOOR.minY} x2={x} y2={FLOOR.maxY} className="map-grid" />
    )
  }

  for (let y = FLOOR.minY + 1; y < FLOOR.maxY; y++) {
    lines.push(
      <line key={`h${y}`} x1={FLOOR.minX} y1={y} x2={FLOOR.maxX} y2={y} className="map-grid" />
    )
  }

  return <g>{lines}</g>
}
