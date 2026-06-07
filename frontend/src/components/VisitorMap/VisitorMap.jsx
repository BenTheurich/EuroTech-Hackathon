import GridFloorPlan from '../GridFloorPlan/GridFloorPlan';
import { confidenceRingRadius } from '../../locationSmoothing';
import styles from './VisitorMap.module.css';

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
            <text y={0.1} textAnchor="middle" fontSize={0.3} className={styles.featureIcon}>
              {f.icon}
            </text>
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
          <text y={0.09} textAnchor="middle" fontSize={0.26} className={styles.destIcon}>
            {destination.icon}
          </text>
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
