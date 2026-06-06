import { useNavigate } from 'react-router-dom';
import styles from './Buildings.module.css';

const BUILDINGS = [
  {
    id: 'science',
    name: 'Science Building',
    address: 'North Campus, Block A',
    floors: 4,
    status: 'active',
    accessPoints: 8,
    thumb: '🔬',
  },
  {
    id: 'library',
    name: 'Central Library',
    address: 'Main Campus, Central Area',
    floors: 3,
    status: 'active',
    accessPoints: 6,
    thumb: '📚',
  },
  {
    id: 'admin',
    name: 'Administration Building',
    address: 'South Campus, Block C',
    floors: 2,
    status: 'draft',
    accessPoints: 0,
    thumb: '🏛️',
  },
];

export default function Buildings() {
  const navigate = useNavigate();

  return (
    <div className={styles.page}>
      <div className={styles.toolbar}>
        <span className={styles.count}>{BUILDINGS.length} buildings</span>
        <button className={styles.addBtn}>+ Add Building</button>
      </div>

      <div className={styles.grid}>
        {BUILDINGS.map((b) => (
          <div key={b.id} className={styles.card}>
            <div className={styles.cardTop}>
              <div className={styles.thumb}>{b.thumb}</div>
              <span className={`${styles.status} ${styles[b.status]}`}>
                {b.status === 'active' ? '● Active' : '○ Draft'}
              </span>
            </div>

            <div className={styles.cardBody}>
              <h3 className={styles.name}>{b.name}</h3>
              <p className={styles.address}>{b.address}</p>

              <div className={styles.meta}>
                <div className={styles.metaItem}>
                  <span className={styles.metaIcon}>⬆</span>
                  <span>{b.floors} floors</span>
                </div>
                <div className={styles.metaItem}>
                  <span className={styles.metaIcon}>📡</span>
                  <span>{b.accessPoints} APs</span>
                </div>
              </div>
            </div>

            <div className={styles.cardFooter}>
              <button
                className={styles.openBtn}
                onClick={() => navigate(`/buildings/${b.id}`)}
              >
                Open floor plans →
              </button>
            </div>
          </div>
        ))}

        {/* Add building placeholder */}
        <button className={styles.addCard} onClick={() => {}}>
          <span className={styles.addCardIcon}>+</span>
          <span className={styles.addCardLabel}>Add Building</span>
        </button>
      </div>
    </div>
  );
}
