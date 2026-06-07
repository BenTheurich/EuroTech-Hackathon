import GridFloorPlan from '../GridFloorPlan/GridFloorPlan';
import { confidenceRingRadius } from '../../locationSmoothing';
import styles from './VisitorMap.module.css';

// A marker icon drawn INSIDE the SVG (grid units). Destination / feature icons
// can be either an image path under /icons/ or an emoji glyph; render the former
// as a centred <image> and the latter as <text> so both kinds show up properly
// (previously an image path was painted verbatim as text).
function MapIcon({ icon, size = 0.36, className }) {
  if (typeof icon === 'string' && icon.startsWith('/icons/')) {
    return (
      <image
        href={icon}
        x={-size / 2}
        y={-size / 2}
        width={size}
        height={size}
        preserveAspectRatio="xMidYMid meet"
      />
    );
  }
  return (
    <text y={size * 0.32} textAnchor="middle" fontSize={size * 0.78} className={className}>
      {icon}
    </text>
  );
}

// The visitor-facing map. Reuses the admin's light GridFloorPlan (read-only) so
// the two interfaces share one design, and overlays:
//   • the visitor's live, smoothed position (from the backend KNN /ws)
//   • their chosen destination
//   • the Dijkstra route (computed on the backend over the drawn walls)
//
// All coordinates are in the shared KNN grid space (x 0–7, y 0–5).
export default function VisitorMap({ walls, position, destination, route, features = [] }) {
  const ringRadius = position ? confidenceRingRadius(position.confidence) : 0;

  // The backend returns the route as a poly-line of grid points; fall back to a
  // straight guide line if it hasn't arrived yet.
  const routePoints = route?.path?.length
    ? route.path.map((p) => `${p.x},${p.y}`).join(' ')
    : position && destination
      ? `${position.x},${position.y} ${destination.x},${destination.y}`
      : null;

  return (
    <GridFloorPlan walls={walls} editable={false}>
      {/* Fixed floor landmarks (stairs, lift). Skip the one currently selected
          as the destination so its prominent marker isn't drawn twice. */}
      {features
        .filter((f) => f.id !== destination?.id)
        .map((f) => (
          <g key={f.id} transform={`translate(${f.x}, ${f.y})`} className={styles.feature}>
            <circle r={0.26} className={styles.featureHalo} />
            <MapIcon icon={f.icon} size={0.34} className={styles.featureIcon} />
          </g>
        ))}

      {/* Dijkstra route from the visitor to the destination, following corridors */}
      {routePoints && (
        <polyline
          points={routePoints}
          className={styles.route}
          fill="none"
        />
      )}

      {/* Destination marker */}
      {destination && (
        <g transform={`translate(${destination.x}, ${destination.y})`}>
          <circle r={0.34} className={styles.destHalo} />
          <circle r={0.22} className={styles.destDot} />
          <MapIcon icon={destination.icon} size={0.3} className={styles.destIcon} />
        </g>
      )}

      {/* Visitor live position */}
      {position && (
        <g
          className={`${styles.user} ${styles[`user_${position.trackerStatus || 'live'}`] || ''}`}
          transform={`translate(${position.x}, ${position.y})`}
        >
          <circle r={ringRadius} className={styles.userConfidence} />
          <circle r={0.3} className={styles.userPulse} />
          <circle r={0.13} className={styles.userDot} />
        </g>
      )}
    </GridFloorPlan>
  );
}
