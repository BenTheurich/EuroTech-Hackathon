import { useLocation } from 'react-router-dom';
import styles from './Header.module.css';

const PAGE_TITLES = {
  '/': 'Dashboard',
  '/buildings': 'Buildings',
  '/access-points': 'Access Points',
  '/analytics': 'Analytics',
  '/settings': 'Settings',
};

export default function Header({ onMenuClick }) {
  const { pathname } = useLocation();
  const base = '/' + pathname.split('/')[1];
  const title = PAGE_TITLES[base] ?? 'NavCity';

  return (
    <header className={styles.header}>
      <div className={styles.left}>
        {/* Hamburger — only visible below the lg breakpoint (CSS). */}
        <button
          className={styles.menuBtn}
          onClick={onMenuClick}
          aria-label="Open menu"
        >
          <span className={styles.menuBars} />
        </button>
        <div className={styles.titleBlock}>
          <h1 className={styles.title}>{title}</h1>
          <span className={styles.breadcrumb}>Smart City · Indoor Navigation Platform</span>
        </div>
      </div>
      <div className={styles.right}>
        <div className={styles.badge}>
          <span className={styles.badgeDot} />
          Live
        </div>
        <button className={styles.avatar}>A</button>
      </div>
    </header>
  );
}
