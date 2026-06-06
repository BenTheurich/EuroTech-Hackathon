import styles from './FloorSelector.module.css';

const DEFAULT_FLOORS = [
  { id: 'ground', label: 'Ground Floor' },
  { id: 'floor1', label: 'Floor 1' },
  { id: 'floor2', label: 'Floor 2' },
  { id: 'floor3', label: 'Floor 3' },
];

export default function FloorSelector({ floors = DEFAULT_FLOORS, activeFloor, onChange }) {
  return (
    <div className={styles.selector}>
      <span className={styles.label}>Floor</span>
      <div className={styles.tabs}>
        {floors.map((floor) => (
          <button
            key={floor.id}
            className={`${styles.tab} ${activeFloor === floor.id ? styles.active : ''}`}
            onClick={() => onChange(floor.id)}
          >
            {floor.label}
          </button>
        ))}
      </div>
    </div>
  );
}
