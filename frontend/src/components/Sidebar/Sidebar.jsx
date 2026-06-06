import { NavLink } from 'react-router-dom';
import styles from './Sidebar.module.css';

const NAV_ITEMS = [
  { to: '/', icon: '⊞', label: 'Dashboard', end: true },
  { to: '/buildings', icon: '🏢', label: 'Buildings' },
  { to: '/live', icon: '📍', label: 'Live Map' },
  { to: '/access-points', icon: '📡', label: 'Access Points' },
  { to: '/analytics', icon: '📊', label: 'Analytics' },
  { to: '/settings', icon: '⚙', label: 'Settings' },
];

export default function Sidebar({ open = false, onClose }) {
  return (
    <>
      {/* Backdrop — only rendered/visible below the lg breakpoint when the drawer is open. */}
      <div
        className={`${styles.backdrop} ${open ? styles.backdropOpen : ''}`}
        onClick={onClose}
        aria-hidden="true"
      />

      <aside className={`${styles.sidebar} ${open ? styles.open : ''}`}>
        <div className={styles.brand}>
          <span className={styles.brandIcon}>◈</span>
          <div className={styles.brandText}>
            <div className={styles.brandName}>NavCity</div>
            <div className={styles.brandSub}>Indoor Navigation</div>
          </div>
          {/* Close button — only visible in drawer mode (mobile/tablet). */}
          <button className={styles.closeBtn} onClick={onClose} aria-label="Close menu">
            ✕
          </button>
        </div>

        <nav className={styles.nav}>
          <div className={styles.navGroup}>
            <span className={styles.navGroupLabel}>Management</span>
            {NAV_ITEMS.slice(0, 3).map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                onClick={onClose}
                className={({ isActive }) =>
                  `${styles.navItem} ${isActive ? styles.active : ''}`
                }
              >
                <span className={styles.navIcon}>{item.icon}</span>
                {item.label}
              </NavLink>
            ))}
          </div>

          <div className={styles.navGroup}>
            <span className={styles.navGroupLabel}>System</span>
            {NAV_ITEMS.slice(3).map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={onClose}
                className={({ isActive }) =>
                  `${styles.navItem} ${isActive ? styles.active : ''}`
                }
              >
                <span className={styles.navIcon}>{item.icon}</span>
                {item.label}
              </NavLink>
            ))}
          </div>
        </nav>

        <div className={styles.footer}>
          <div className={styles.statusDot} />
          <span>System Online</span>
        </div>
      </aside>
    </>
  );
}
