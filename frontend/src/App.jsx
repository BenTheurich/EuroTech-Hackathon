import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard/Dashboard';
import Buildings from './pages/Buildings/Buildings';
import FloorPlanViewer from './pages/FloorPlanViewer/FloorPlanViewer';
import LiveMap from './pages/LiveMap/LiveMap';

// Two sites in one app:
//   /        → admin dashboard (Layout shell: sidebar + header + pages)
//   /live    → full-screen user tracking map (the friend's live KNN map)
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="buildings" element={<Buildings />} />
          <Route path="buildings/:id" element={<FloorPlanViewer />} />
          <Route path="access-points" element={<PlaceholderPage title="Access Points" />} />
          <Route path="analytics" element={<PlaceholderPage title="Analytics" />} />
          <Route path="settings" element={<PlaceholderPage title="Settings" />} />
        </Route>
        <Route path="/live" element={<LiveMap />} />
      </Routes>
    </BrowserRouter>
  );
}

function PlaceholderPage({ title }) {
  return (
    <div className="flex h-[60vh] flex-col items-center justify-center gap-3 text-slate-400">
      <span className="text-5xl">🚧</span>
      <span className="text-lg font-semibold">{title}</span>
      <span className="text-sm">Coming soon</span>
    </div>
  );
}
