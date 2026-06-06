import './App.css'
import { useLocationSocket } from './useLocationSocket'
import { useSmoothedLocation } from './useSmoothedLocation'
import MapView from './MapView'

const STATUS_LABELS = {
  connecting: 'Connecting…',
  connected: 'Live',
  disconnected: 'Reconnecting…',
}

function App() {
  const { status, targetPosition } = useLocationSocket()
  const { position, trail } = useSmoothedLocation(targetPosition)
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard/Dashboard';
import Buildings from './pages/Buildings/Buildings';
import FloorPlanViewer from './pages/FloorPlanViewer/FloorPlanViewer';

// NOTE: the original full-screen live Wi-Fi map (MapView.jsx + useLocationSocket.js
// + App.css) is preserved on disk but intentionally not routed yet. The user-facing
// "tracking" site and its live-position source are a deferred decision we'll revisit.

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
      </Routes>
    </BrowserRouter>
  );
}

      <footer className="app-footer">
        {position ? (
          <span>
            Position: x = {position.x.toFixed(1)}, y = {position.y.toFixed(1)}
            {' '}
            confidence = {Math.round((position.confidence ?? 1) * 100)}%
          </span>
        ) : (
          <span>Waiting for the first reading from the scanner…</span>
        )}
      </footer>
function PlaceholderPage({ title }) {
  return (
    <div className="flex h-[60vh] flex-col items-center justify-center gap-3 text-slate-400">
      <span className="text-5xl">🚧</span>
      <span className="text-lg font-semibold">{title}</span>
      <span className="text-sm">Coming soon</span>
    </div>
  );
}
