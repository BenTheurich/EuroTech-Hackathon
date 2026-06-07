import styles from './GridFloorPlan.module.css';
import { GRID, ANCHORS, allEdges } from './gridModel';

// Interactive grid floor editor. The admin "draws the map" by toggling WALL
// SEGMENTS that live on the edges between adjacent vertices. Because the grid is
// locked to the KNN coordinate space (see gridModel.js), a live (x, y) from the
// backend can be overlaid directly on top of whatever the admin draws.
const PADDING = 0.6;

export default function GridFloorPlan({ walls, onToggleEdge = () => {}, editable = true, children }) {
  const viewBox = `${-PADDING} ${-PADDING} ${GRID.cols + PADDING * 2} ${GRID.rows + PADDING * 2}`;
  const edges = allEdges();

  return (
    <div className={styles.container}>
      <svg
        className={styles.svg}
        viewBox={viewBox}
        preserveAspectRatio="xMidYMid meet"
        xmlns="http://www.w3.org/2000/svg"
        role="img"
        aria-label="Editable grid floor plan"
      >
        {/* Floor area */}
        <rect x={0} y={0} width={GRID.cols} height={GRID.rows} className={styles.floor} />

        {/* Faint cell grid */}
        <g className={styles.gridLines}>
          {Array.from({ length: GRID.cols + 1 }, (_, x) => (
            <line key={`gx-${x}`} x1={x} y1={0} x2={x} y2={GRID.rows} />
          ))}
          {Array.from({ length: GRID.rows + 1 }, (_, y) => (
            <line key={`gy-${y}`} x1={0} y1={y} x2={GRID.cols} y2={y} />
          ))}
        </g>

        {/* Drawn wall segments */}
        <g className={styles.walls}>
          {edges
            .filter((e) => walls.has(e.key))
            .map((e) => (
              <line key={e.key} x1={e.x1} y1={e.y1} x2={e.x2} y2={e.y2} className={styles.wall} />
            ))}
        </g>

        {/* Vertex dots for visual reference */}
        <g className={styles.vertices}>
          {Array.from({ length: GRID.cols + 1 }, (_, x) =>
            Array.from({ length: GRID.rows + 1 }, (_, y) => (
              <circle key={`v-${x}-${y}`} cx={x} cy={y} r={0.04} />
            ))
          )}
        </g>

        {/* Wi-Fi anchors A–D at the corners (KNN reference points) */}
        {ANCHORS.map((a) => (
          <g key={a.id} transform={`translate(${a.x}, ${a.y})`} className={styles.anchorGroup}>
            <rect x={-0.17} y={-0.17} width={0.34} height={0.34} rx={0.06} className={styles.anchor} />
            <text y={0.075} textAnchor="middle" fontSize={0.22} className={styles.anchorLabel}>
              {a.id}
            </text>
          </g>
        ))}

        {/* Live position / tracking overlay slot */}
        {children}

        {/* Clickable edge hot-zones (on top so toggling a wall off also works) */}
        {editable && (
          <g className={styles.hotspots}>
            {edges.map((e) => (
              <line
                key={`hit-${e.key}`}
                x1={e.x1}
                y1={e.y1}
                x2={e.x2}
                y2={e.y2}
                className={`${styles.hotspot} ${walls.has(e.key) ? styles.hotspotActive : ''}`}
                onClick={() => onToggleEdge(e.key)}
              />
            ))}
          </g>
        )}
      </svg>
    </div>
  );
}
