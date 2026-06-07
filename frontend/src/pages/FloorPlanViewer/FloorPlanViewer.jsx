import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import FloorSelector from '../../components/FloorSelector/FloorSelector';
import GridFloorPlan from '../../components/GridFloorPlan/GridFloorPlan';
import { perimeterWalls } from '../../components/GridFloorPlan/gridModel';
import PositionOverlay from '../../components/PositionOverlay/PositionOverlay';
import styles from './FloorPlanViewer.module.css';

const BUILDING_NAMES = {
  science: 'Science Building',
  library: 'Central Library',
  admin: 'Administration Building',
};

const FLOORS = [
  { id: 'ground', label: 'Ground Floor' },
  { id: 'floor1', label: 'Floor 1' },
  { id: 'floor2', label: 'Floor 2' },
  { id: 'floor3', label: 'Floor 3' },
];

export default function FloorPlanViewer() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [activeFloor, setActiveFloor] = useState('floor1');
  const [trackingActive, setTrackingActive] = useState(true);

  // Wall segments drawn by the admin. Each floor starts as a bare room outline
  // (perimeter); switching floors resets the canvas for that floor.
  const [walls, setWalls] = useState(() => perimeterWalls());

  const handleFloorChange = (floorId) => {
    setActiveFloor(floorId);
    setWalls(perimeterWalls());
  };

  const buildingName = BUILDING_NAMES[id] ?? 'Building';

  const toggleEdge = (key) => {
    setWalls((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  return (
    <div className={styles.page}>
      {/* Breadcrumb */}
      <div className={styles.breadcrumb}>
        <button className={styles.backBtn} onClick={() => navigate('/buildings')}>
          ← Buildings
        </button>
        <span className={styles.sep}>/</span>
        <span className={styles.crumbCurrent}>{buildingName}</span>
      </div>

      <div className={styles.layout}>
        {/* Toolbar */}
        <div className={styles.toolbar}>
          <FloorSelector
            floors={FLOORS}
            activeFloor={activeFloor}
            onChange={handleFloorChange}
          />
          <div className={styles.actions}>
            <button className={styles.btnOutline} onClick={() => setWalls(perimeterWalls())}>
              ▭ Reset to outline
            </button>
            <button className={styles.btnOutline} onClick={() => setWalls(new Set())}>
              🧹 Clear walls
            </button>
            <button className={styles.btnOutline}>📡 Add access point</button>
            <button className={styles.btnOutline}>🏷️ Add room / POI</button>
            <button
              className={`${styles.btnOutline} ${trackingActive ? styles.btnActive : ''}`}
              onClick={() => setTrackingActive((v) => !v)}
            >
              {trackingActive ? '⏸ Pause tracking' : '▶ Preview navigation'}
            </button>
          </div>
        </div>

        {/* Map area */}
        <div className={styles.mapWrapper}>
          <div className={styles.mapCard}>
            <div className={styles.mapHeader}>
              <span className={styles.mapTitle}>
                {buildingName} · {FLOORS.find((f) => f.id === activeFloor)?.label}
              </span>
              <div className={styles.legend}>
                <span className={styles.legendItem}>
                  <span className={styles.lineWall} /> Wall
                </span>
                <span className={styles.legendItem}>
                  <span className={styles.dotRed} /> Raw (noisy)
                </span>
                <span className={styles.legendItem}>
                  <span className={styles.dotBlue} /> Filtered position
                </span>
                <span className={styles.legendItem}>
                  <span className={styles.dotWifi} /> Wi-Fi anchor
                </span>
              </div>
            </div>

            <div className={styles.mapBody}>
              <p className={styles.editHint}>
                Click the lines between cells to add or remove walls. Anchors A–D are
                fixed to the corners of the KNN grid (x 0–7, y 0–5).
              </p>
              <GridFloorPlan walls={walls} onToggleEdge={toggleEdge}>
                {trackingActive && <PositionOverlay active={trackingActive} />}
              </GridFloorPlan>
            </div>
          </div>

          {/* Side info panel */}
          <div className={styles.infoPanel}>
            <div className={styles.infoCard}>
              <h4 className={styles.infoTitle}>Floor Info</h4>
              <div className={styles.infoRow}>
                <span className={styles.infoLabel}>Grid</span>
                <span className={styles.infoValue}>7 × 5 cells</span>
              </div>
              <div className={styles.infoRow}>
                <span className={styles.infoLabel}>Wall segments</span>
                <span className={styles.infoValue}>{walls.size}</span>
              </div>
              <div className={styles.infoRow}>
                <span className={styles.infoLabel}>Anchors</span>
                <span className={styles.infoValue}>4 (A–D)</span>
              </div>
              <div className={styles.infoRow}>
                <span className={styles.infoLabel}>Floor plan</span>
                <span className={`${styles.infoValue} ${walls.size ? styles.green : styles.gray}`}>
                  {walls.size ? '✓ Drawn' : '○ Empty'}
                </span>
              </div>
            </div>

            <div className={styles.infoCard}>
              <h4 className={styles.infoTitle}>Live Status</h4>
              <div className={styles.infoRow}>
                <span className={styles.infoLabel}>Tracking</span>
                <span className={`${styles.infoValue} ${trackingActive ? styles.green : styles.gray}`}>
                  {trackingActive ? '● Active' : '○ Paused'}
                </span>
              </div>
              <div className={styles.infoRow}>
                <span className={styles.infoLabel}>Algorithm</span>
                <span className={styles.infoValue}>KNN (mock)</span>
              </div>
              <div className={styles.infoRow}>
                <span className={styles.infoLabel}>Signal</span>
                <span className={styles.infoValue}>4 anchors</span>
              </div>
              <div className={styles.infoRow}>
                <span className={styles.infoLabel}>Coord space</span>
                <span className={styles.infoValue}>x 0–7 · y 0–5</span>
              </div>
            </div>

            <div className={styles.infoCard}>
              <h4 className={styles.infoTitle}>WebSocket</h4>
              <p className={styles.infoNote}>
                Mock mode active. The backend KNN model broadcasts live coordinates at{' '}
                <code>ws://localhost:8000/ws</code> in the same grid space; wiring it to
                this map is a deferred step.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
