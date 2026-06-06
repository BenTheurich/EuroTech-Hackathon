import { useState, useEffect, useRef } from 'react';

// Mock positioning hook — works in the KNN coordinate space (x ∈ [0,7], y ∈ [0,5])
// so the dot lines up with the grid the admin draws and with the real anchors.
//
// DEFERRED: the real source (the backend /ws KNN websocket) will replace this
// once we settle the live-position decision. Swap the body of the interval for:
//   const ws = new WebSocket('ws://<host>:8000/ws');
//   ws.onmessage = (e) => { const d = JSON.parse(e.data); setFilteredPos(d); };

const WAYPOINTS = [
  { x: 1, y: 1 },
  { x: 5, y: 1 },
  { x: 6, y: 2.5 },
  { x: 5, y: 4 },
  { x: 2, y: 4 },
  { x: 1, y: 2.5 },
  { x: 1, y: 1 },
];

function lerp(a, b, t) {
  return a + (b - a) * t;
}

function addNoise(val, amount = 0.4) {
  return val + (Math.random() - 0.5) * amount;
}

export function useMockPositioning(active = true) {
  const [rawPos, setRawPos] = useState({ x: 1, y: 1 });
  const [filteredPos, setFilteredPos] = useState({ x: 1, y: 1 });
  const progressRef = useRef(0);
  const waypointRef = useRef(0);

  useEffect(() => {
    if (!active) return;

    const interval = setInterval(() => {
      const currentWp = WAYPOINTS[waypointRef.current];
      const nextWp = WAYPOINTS[(waypointRef.current + 1) % WAYPOINTS.length];

      progressRef.current += 0.03;
      if (progressRef.current >= 1) {
        progressRef.current = 0;
        waypointRef.current = (waypointRef.current + 1) % (WAYPOINTS.length - 1);
      }

      const t = progressRef.current;
      const smoothX = lerp(currentWp.x, nextWp.x, t);
      const smoothY = lerp(currentWp.y, nextWp.y, t);

      setFilteredPos({ x: smoothX, y: smoothY });
      setRawPos({ x: addNoise(smoothX), y: addNoise(smoothY) });
    }, 150);

    return () => clearInterval(interval);
  }, [active]);

  return { rawPos, filteredPos };
}
