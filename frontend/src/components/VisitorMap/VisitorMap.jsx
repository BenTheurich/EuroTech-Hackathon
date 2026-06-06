import GridFloorPlan from '../GridFloorPlan/GridFloorPlan';
import { confidenceRingRadius } from '../../locationSmoothing';
import styles from './VisitorMap.module.css';

// The visitor-facing map. Reuses the admin's light GridFloorPlan (read-only) so
// the two interfaces share one design, and overlays:
//   • the visitor's live, smoothed position (from the backend KNN /ws)
//   • their chosen destination
//   • a direct guide line between the two
//
// All coordinates are in the shared KNN grid space (x 0–7, y 0–5).
export default function VisitorMap({ walls, position, destination }) {
  const ringRadius = position ? confidenceRingRadius(position.confidence) : 0;

  return (
    <GridFloorPlan walls={walls} editable={false}>
      {/* Guide line from the visitor to the destination */}
      {position && destination && (
        <line
          x1={position.x}
          y1={position.y}
          x2={destination.x}
          y2={destination.y}
          className={styles.route}
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
