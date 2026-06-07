import { useState, useEffect, useRef, useMemo } from 'react';
import { findRoute, lineOfSightClear } from '../components/GridFloorPlan/gridRouting';

// Mock positioning hook — works in the KNN coordinate space (x ∈ [0,7], y ∈ [0,5])
// so the dot lines up with the grid the admin draws and with the real anchors.
//
// The patrol is WALL-AWARE: instead of lerping blindly between fixed waypoints
// (which let the dots phase straight through walls the admin drew), we route
// each leg of the loop with the same Dijkstra/line-of-sight router the visitor
// view uses. The filtered dot therefore walks corridors and bends around walls;
// the raw (noisy) dot's jitter is clamped so it never jumps across a wall either.
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

const SPEED = 0.07; // grid units travelled per tick (~0.47 m/s at 150ms)
const NOISE = 0.4;

function lerp(a, b, t) {
  return a + (b - a) * t;
}

function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v));
}

// Build a wall-respecting patrol polyline by routing between consecutive
// waypoints. Legs the walls have sealed off entirely are skipped (rather than
// drawn as a straight line that would cross a wall), so the dot always follows
// the open floor. With no interior walls this collapses to the plain loop.
function buildPatrol(walls) {
  const pts = [];
  let last = null;
  for (const wp of WAYPOINTS) {
    if (!last) {
      pts.push(wp);
      last = wp;
      continue;
    }
    const leg = findRoute(last, wp, walls);
    if (leg.reachable && leg.path.length > 1) {
      for (let k = 1; k < leg.path.length; k++) pts.push(leg.path[k]);
      last = wp;
    }
    // unreachable: skip this waypoint, keep heading to the next reachable one
  }
  return pts.length > 1 ? pts : [WAYPOINTS[0]];
}

// Cumulative-length geometry so we can advance at a constant speed and sample a
// point at any distance along the loop.
function patrolGeometry(pts) {
  const segs = [];
  let total = 0;
  for (let i = 1; i < pts.length; i++) {
    const len = Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y);
    if (len === 0) continue;
    segs.push({ a: pts[i - 1], b: pts[i], len, start: total });
    total += len;
  }
  return { segs, total, first: pts[0] };
}

function pointAt(geom, d) {
  const { segs, total, first } = geom;
  if (!segs.length || total === 0) return { ...first };
  const dd = ((d % total) + total) % total;
  for (const s of segs) {
    if (dd <= s.start + s.len) {
      const t = (dd - s.start) / s.len;
      return { x: lerp(s.a.x, s.b.x, t), y: lerp(s.a.y, s.b.y, t) };
    }
  }
  const lastSeg = segs[segs.length - 1];
  return { ...lastSeg.b };
}

export function useMockPositioning(active = true, walls = new Set()) {
  const [rawPos, setRawPos] = useState({ x: 1, y: 1 });
  const [filteredPos, setFilteredPos] = useState({ x: 1, y: 1 });
  const distanceRef = useRef(0);

  // Recompute the patrol only when the walls actually change (their identity is
  // stable between admin edits, so the 150ms ticks don't rebuild it).
  const geom = useMemo(() => patrolGeometry(buildPatrol(walls)), [walls]);

  useEffect(() => {
    if (!active) return;

    const interval = setInterval(() => {
      distanceRef.current += SPEED;
      const smooth = pointAt(geom, distanceRef.current);

      // Noisy reading around the true point — but clamped so the jitter never
      // hops across a wall (which would look like the raw dot phasing through).
      let nx = clamp(smooth.x + (Math.random() - 0.5) * NOISE, 0, 7);
      let ny = clamp(smooth.y + (Math.random() - 0.5) * NOISE, 0, 5);
      if (!lineOfSightClear(smooth.x, smooth.y, nx, ny, walls)) {
        nx = smooth.x;
        ny = smooth.y;
      }

      setFilteredPos(smooth);
      setRawPos({ x: nx, y: ny });
    }, 150);

    return () => clearInterval(interval);
  }, [active, geom, walls]);

  return { rawPos, filteredPos };
}
