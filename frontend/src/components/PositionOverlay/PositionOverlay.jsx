import { useMockPositioning } from '../../hooks/useMockPositioning';
import styles from './PositionOverlay.module.css';

// Renders inside GridFloorPlan's SVG, so all values are in KNN units (0..7, 0..5).
export default function PositionOverlay({ active = true }) {
  const { rawPos, filteredPos } = useMockPositioning(active);

  return (
    <g className={styles.overlay}>
      {/* Raw noisy reading */}
      <circle cx={rawPos.x} cy={rawPos.y} r={0.18} className={styles.raw} />
      <circle cx={rawPos.x} cy={rawPos.y} r={0.06} className={styles.rawDot} />

      {/* Filtered position with pulse ring */}
      <circle cx={filteredPos.x} cy={filteredPos.y} r={0.3} className={styles.pulse} />
      <circle cx={filteredPos.x} cy={filteredPos.y} r={0.18} className={styles.filtered} />
      <circle cx={filteredPos.x} cy={filteredPos.y} r={0.07} className={styles.filteredDot} />
    </g>
  );
}
