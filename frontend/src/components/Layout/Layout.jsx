import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from '../Sidebar/Sidebar';
import Header from '../Header/Header';
import styles from './Layout.module.css';

export default function Layout() {
  // Drawer state drives the mobile/tablet slide-out sidebar. On desktop the
  // sidebar is always visible (CSS), so this only matters below the `lg` width.
  // The drawer is closed by tapping a nav item or the backdrop (see Sidebar).
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <div className={styles.shell}>
      <Sidebar open={drawerOpen} onClose={() => setDrawerOpen(false)} />
      <div className={styles.main}>
        <Header onMenuClick={() => setDrawerOpen((v) => !v)} />
        <main className={styles.content}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
