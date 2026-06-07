import { useNavigate } from 'react-router-dom';
import styles from './Dashboard.module.css';

const STATS = [
  { label: 'Buildings', value: '3', icon: '🏢', color: '#c0623c' },
  { label: 'Access Points', value: '12', icon: '📡', color: '#76875c' },
  { label: 'Active Users', value: '24', icon: '👤', color: '#c2974a' },
  { label: 'Avg. Location Error', value: '1.8m', icon: '📍', color: '#a9694e' },
];

const RECENT_ACTIVITY = [
  { text: 'Floor plan updated', detail: 'Science Building · Floor 2', time: '2 min ago', type: 'update' },
  { text: 'New access point added', detail: 'Library · Ground Floor', time: '18 min ago', type: 'add' },
  { text: 'Calibration completed', detail: 'Admin Building · Floor 1', time: '1 hr ago', type: 'done' },
  { text: 'User session started', detail: 'Science Building', time: '2 hr ago', type: 'user' },
];

export default function Dashboard() {
  const navigate = useNavigate();

  return (
    <div className={styles.page}>
      <section className={styles.hero}>
        <div className={styles.heroText}>
          <span className={styles.heroKicker}>Indoor navigation platform</span>
          <h1 className={styles.heroTitle}>Welcome back</h1>
          <p className={styles.heroLede}>
            Your venues are live and tracking. Draw floor plans, place anchors and
            guide visitors — all from one calm console.
          </p>
          <div className={styles.heroActions}>
            <button className={styles.heroBtn} onClick={() => navigate('/buildings')}>
              Open buildings
            </button>
            <button className={styles.heroBtnGhost} onClick={() => navigate('/visit')}>
              Preview visitor view ↗
            </button>
          </div>
        </div>
        <div className={styles.heroArt} aria-hidden="true">
          <span className={styles.heroOrb} />
          <span className={styles.heroPin}>📍</span>
        </div>
      </section>

      <div className={styles.statsGrid}>
        {STATS.map((s) => (
          <div key={s.label} className={styles.statCard}>
            <div className={styles.statIcon} style={{ background: s.color + '18', color: s.color }}>
              {s.icon}
            </div>
            <div>
              <div className={styles.statValue}>{s.value}</div>
              <div className={styles.statLabel}>{s.label}</div>
            </div>
          </div>
        ))}
      </div>

      <div className={styles.grid}>
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>Recent Activity</h2>
          </div>
          <div className={styles.activityList}>
            {RECENT_ACTIVITY.map((a, i) => (
              <div key={i} className={styles.activityItem}>
                <div className={`${styles.activityDot} ${styles[a.type]}`} />
                <div className={styles.activityContent}>
                  <span className={styles.activityText}>{a.text}</span>
                  <span className={styles.activityDetail}>{a.detail}</span>
                </div>
                <span className={styles.activityTime}>{a.time}</span>
              </div>
            ))}
          </div>
        </div>

        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>Quick Actions</h2>
          </div>
          <div className={styles.actions}>
            <button className={styles.actionBtn} onClick={() => navigate('/buildings')}>
              <span>🏢</span> Manage Buildings
            </button>
            <button className={styles.actionBtn} onClick={() => navigate('/buildings')}>
              <span>🗺️</span> Open Floor Plans
            </button>
            <button className={styles.actionBtn}>
              <span>📡</span> Configure Access Points
            </button>
            <button className={styles.actionBtn}>
              <span>📊</span> View Analytics
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
