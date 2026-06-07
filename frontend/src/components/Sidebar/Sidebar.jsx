import { NavLink } from 'react-router-dom';
import styles from './Sidebar.module.css';

const NAV_ITEMS = [
  { to: '/', icon: '⊞', label: 'Dashboard', end: true },
  { to: '/buildings', icon: 'src/assets/icons/buildingsstats.jpeg', label: 'Buildings' },
  { to: '/visit', icon: 'src/assets/icons/user_profile.jpeg', label: 'Visitor View' },
  { to: '/live', icon: 'src/assets/icons/livemap.jpeg', label: 'Live Map' },
  { to: '/access-points', icon: 'src/assets/icons/accesspt.jpeg', label: 'Access Points' },
  { to: '/analytics', icon: 'src/assets/icons/analytics.jpeg', label: 'Analytics' },
  { to: '/settings', icon: 'src/assets/icons/settings.jpeg', label: 'Settings' },
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
            <div className={styles.brandName}>RmFindr</div>
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
