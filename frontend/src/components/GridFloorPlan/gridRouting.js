// ============================================================================
// GRID ROUTING — any-angle shortest path that never crosses or cuts a wall.
//
// Walls are impassable segments on the lattice edges (the same `h-x-y` /
// `v-x-y` keys the editor draws). A route must NOT cross a wall, and must NOT
// squeeze diagonally between two walls that meet at a corner.
//
// The route runs STRAIGHT where the floor is open and bends only where a wall
// is genuinely in the way — so it reads like a person walking.
//
// Two pieces:
//   1. lineOfSightClear() — a DDA grid march. It walks the cells a straight
//      line passes through and checks the actual cell EDGE it crosses each
//      step. Crucially, when the line passes exactly through a lattice vertex
//      (a diagonal corner), it requires BOTH squeezed edges to be open — this
//      is what stops the path slipping "between two walls" at a corner.
//   2. findRoute() — a visibility graph over the cell centres (+ the real
//      start and goal). Two nodes connect when lineOfSightClear() is true;
//      Dijkstra over it gives the shortest non-crossing, non-corner-cutting
//      path. Cell centres sit off every wall line, so paths are robust; on
//      open floor the start sees the goal directly and the route is a single
//      straight segment.
//
// The lattice is tiny, so this recomputes instantly on every position/wall
// change. Browser counterpart of backend/pathfinding.py (identical semantics).
// ============================================================================
import { GRID } from './gridModel.js';

const EPS = 1e-9;

/**
 * True if a straight line from (ax,ay) to (bx,by) crosses no wall and cuts no
 * corner. `walls` is a Set of `h-x-y` / `v-x-y` edge keys.
 *
 * Edge / cell convention: cell (cx,cy) is the square [cx,cx+1]x[cy,cy+1].
 *   • crossing the vertical line x=k between rows → wall `v-k-row`
 *   • crossing the horizontal line y=m between cols → wall `h-col-m`
 */
export function lineOfSightClear(ax, ay, bx, by, walls, cols = GRID.cols, rows = GRID.rows) {
  const dx = bx - ax;
  const dy = by - ay;
  if (dx === 0 && dy === 0) return true;

  const stepX = dx > 0 ? 1 : dx < 0 ? -1 : 0;
  const stepY = dy > 0 ? 1 : dy < 0 ? -1 : 0;

  // Cell currently containing the moving point (clamped onto the floor).
  let cx = Math.min(cols - 1, Math.max(0, Math.floor(ax)));
  let cy = Math.min(rows - 1, Math.max(0, Math.floor(ay)));

  // Parameter (t in [0,1]) of the next vertical / horizontal grid-line crossing.
  const nextXLine = stepX > 0 ? cx + 1 : cx;
  const nextYLine = stepY > 0 ? cy + 1 : cy;
  let tMaxX = stepX !== 0 ? (nextXLine - ax) / dx : Infinity;
  let tMaxY = stepY !== 0 ? (nextYLine - ay) / dy : Infinity;
  const tDeltaX = stepX !== 0 ? Math.abs(1 / dx) : Infinity;
  const tDeltaY = stepY !== 0 ? Math.abs(1 / dy) : Infinity;

  while (tMaxX <= 1 + EPS || tMaxY <= 1 + EPS) {
    if (Math.abs(tMaxX - tMaxY) < EPS) {
      // Diagonal vertex crossing. The move from cell (cx,cy) to the opposite
      // cell is legitimate only if one of the two L-shaped detours around the
      // vertex is fully open; otherwise it would cut a wall corner.
      const xLine = stepX > 0 ? cx + 1 : cx; // vertical grid line being crossed
      const yLine = stepY > 0 ? cy + 1 : cy; // horizontal grid line being crossed
      const destCx = cx + stepX;
      const destCy = cy + stepY;
      // Detour via cell (destCx, cy): cross the vertical edge, then the horizontal.
      const viaX = !walls.has(`v-${xLine}-${cy}`) && !walls.has(`h-${destCx}-${yLine}`);
      // Detour via cell (cx, destCy): cross the horizontal edge, then the vertical.
      const viaY = !walls.has(`h-${cx}-${yLine}`) && !walls.has(`v-${xLine}-${destCy}`);
      if (!viaX && !viaY) return false;
      cx = destCx;
      cy = destCy;
      tMaxX += tDeltaX;
      tMaxY += tDeltaY;
    } else if (tMaxX < tMaxY) {
      const vWall = stepX > 0 ? `v-${cx + 1}-${cy}` : `v-${cx}-${cy}`;
      if (walls.has(vWall)) return false;
      cx += stepX;
      tMaxX += tDeltaX;
    } else {
      const hWall = stepY > 0 ? `h-${cx}-${cy + 1}` : `h-${cx}-${cy}`;
      if (walls.has(hWall)) return false;
      cy += stepY;
      tMaxY += tDeltaY;
    }
  }
  return true;
}

function polylineLength(points) {
  let total = 0;
  for (let i = 1; i < points.length; i++) {
    total += Math.hypot(points[i].x - points[i - 1].x, points[i].y - points[i - 1].y);
  }
  return total;
}

/**
 * Drawable shortest-path route from the user's live position to their destination.
 *
 * @param {{x:number,y:number}} start  live position (continuous grid coords)
 * @param {{x:number,y:number}} goal   destination POI (continuous grid coords)
 * @param {Set<string>|Iterable<string>} walls  wall edge keys on the floor
 * @param {string} [preference]        echoed back; geometry is identical on one floor
 * @returns {{reachable:boolean, preference:string, path:Array<{x,y}>, distance:number}}
 *
 * Straight where the floor is open, turning only where a wall blocks the way,
 * and never crossing a wall or cutting a corner. Falls back to a direct segment
 * (with `reachable:false`) if the destination is walled off entirely.
 */
export function findRoute(start, goal, walls, preference = 'fastest', cols = GRID.cols, rows = GRID.rows) {
  const wallSet = walls instanceof Set ? walls : new Set(walls || []);
  const s = { x: start.x, y: start.y };
  const g = { x: goal.x, y: goal.y };

  // Nodes: start (0), goal (1), then every cell centre. Cell centres sit off
  // all wall lines, so the visibility graph can't accidentally hug a wall.
  const nodes = [s, g];
  for (let cy = 0; cy < rows; cy++) {
    for (let cx = 0; cx < cols; cx++) {
      nodes.push({ x: cx + 0.5, y: cy + 0.5 });
    }
  }

  const n = nodes.length;
  const dist = new Array(n).fill(Infinity);
  const prev = new Array(n).fill(-1);
  const done = new Array(n).fill(false);
  dist[0] = 0;

  for (let iter = 0; iter < n; iter++) {
    let u = -1;
    let best = Infinity;
    for (let i = 0; i < n; i++) {
      if (!done[i] && dist[i] < best) {
        best = dist[i];
        u = i;
      }
    }
    if (u === -1 || u === 1) break; // exhausted, or goal finalized
    done[u] = true;

    for (let v = 0; v < n; v++) {
      if (done[v] || v === u) continue;
      if (!lineOfSightClear(nodes[u].x, nodes[u].y, nodes[v].x, nodes[v].y, wallSet, cols, rows)) {
        continue;
      }
      const w = Math.hypot(nodes[v].x - nodes[u].x, nodes[v].y - nodes[u].y);
      if (dist[u] + w < dist[v]) {
        dist[v] = dist[u] + w;
        prev[v] = u;
      }
    }
  }

  const reachable = dist[1] < Infinity;
  let path;
  if (reachable) {
    path = [];
    for (let k = 1; k !== -1; k = prev[k]) path.push(nodes[k]);
    path.reverse();
  } else {
    path = [s, g];
  }

  return {
    reachable,
    preference,
    path: path.map((p) => ({ x: p.x, y: p.y })),
    distance: Math.round(polylineLength(path) * 100) / 100,
  };
}
