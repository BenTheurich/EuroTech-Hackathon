import assert from 'node:assert/strict';

import { findRoute, lineOfSightClear } from './gridRouting.js';
import { generateFloorWalls } from './floorGen.js';
import { GRID, horizontalEdgeKey, verticalEdgeKey } from './gridModel.js';

// Deterministic RNG so random-map failures are reproducible.
function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function pathClearsWalls(path, walls) {
  for (let i = 1; i < path.length; i++) {
    if (!lineOfSightClear(path[i - 1].x, path[i - 1].y, path[i].x, path[i].y, walls)) return false;
  }
  return true;
}

// --- open floor => a single STRAIGHT segment, not a staircase ---------------
const open = findRoute({ x: 0.5, y: 0.5 }, { x: 6.5, y: 4.5 }, new Set());
assert.equal(open.reachable, true);
assert.equal(open.path.length, 2, 'with no walls the route is one straight segment');
assert.ok(Math.abs(open.distance - Math.hypot(6, 4)) < 0.02, 'straight-line distance');

// --- a wall blocks the straight line; removing it restores it ---------------
const wall = new Set([verticalEdgeKey(3, 0), verticalEdgeKey(3, 1), verticalEdgeKey(3, 2)]);
assert.equal(lineOfSightClear(1, 1.5, 5, 1.5, wall), false, 'line of sight is blocked by the wall');
assert.equal(lineOfSightClear(1, 1.5, 5, 1.5, new Set()), true);
const bent = findRoute({ x: 1, y: 1.5 }, { x: 5, y: 1.5 }, wall);
assert.ok(bent.reachable && bent.path.length > 2, 'must bend around the wall');
assert.ok(pathClearsWalls(bent.path, wall), 'no path segment crosses the wall');
assert.ok(bent.distance > Math.hypot(4, 0), 'detour is longer than the blocked straight line');
const cleared = findRoute({ x: 1, y: 1.5 }, { x: 5, y: 1.5 }, new Set());
assert.ok(cleared.path.length === 2 && cleared.distance < bent.distance, 'remove wall => straight again');

// --- THE CORNER-CUT BUG: must not squeeze diagonally between two walls ------
// Two walls meet at the vertex (3,3): v-3-2 (below) and h-2-3 (to the left).
// They pinch the corner the diagonal (2.5,2.5)->(3.5,3.5) would slip through.
// The old segment-intersection test allowed it (endpoint touch); the grid
// march must reject it because BOTH L-detours around the vertex are blocked.
const pinch = new Set([verticalEdgeKey(3, 2), horizontalEdgeKey(2, 3)]);
assert.equal(
  lineOfSightClear(2.5, 2.5, 3.5, 3.5, pinch),
  false,
  'diagonal must not squeeze between the two walls meeting at the corner',
);
const cornerRoute = findRoute({ x: 2.5, y: 2.5 }, { x: 3.5, y: 3.5 }, pinch);
assert.ok(cornerRoute.path.length > 2, 'route detours instead of cutting the corner');
assert.ok(pathClearsWalls(cornerRoute.path, pinch));

// A SINGLE wall at that vertex is not a pinch — the diagonal may legitimately
// round it via the open neighbouring cell (it only touches the wall's endpoint).
assert.equal(
  lineOfSightClear(2.5, 2.5, 3.5, 3.5, new Set([verticalEdgeKey(3, 2)])),
  true,
  'a single wall does not block rounding its free end',
);

// --- a doorway is the ONLY way into a sealed room; route must use it --------
const room = new Set();
// 3x2 room over cells x∈[2,4], y∈[3,4]; walls on all sides, doorway at top x=3..4.
[2, /* gap at 3 */ 4].forEach((x) => room.add(horizontalEdgeKey(x, 3))); // top, gap at (3,3)-(4,3)
[3, 4].forEach((y) => room.add(verticalEdgeKey(2, y)));                  // left
[3, 4].forEach((y) => room.add(verticalEdgeKey(5, y)));                  // right
[2, 3, 4].forEach((x) => room.add(horizontalEdgeKey(x, 5)));            // bottom
const intoRoom = findRoute({ x: 1, y: 1 }, { x: 3.5, y: 4.5 }, room);
assert.ok(intoRoom.reachable, 'destination in the room is reachable through the doorway');
assert.ok(pathClearsWalls(intoRoom.path, room), 'route into the room never crosses a wall');
// A straight shot is blocked, so the route must detour through the only opening.
assert.equal(lineOfSightClear(1, 1, 3.5, 4.5, room), false, 'straight line into the room is blocked');
assert.ok(intoRoom.path.length > 2, 'route detours through the doorway rather than going straight');
// Every crossing of the room's top wall line (y=3) must fall inside the doorway gap x∈[3,4].
for (let i = 1; i < intoRoom.path.length; i++) {
  const a = intoRoom.path[i - 1];
  const b = intoRoom.path[i];
  if ((a.y - 3) * (b.y - 3) < 0) {
    const xAt = a.x + ((3 - a.y) / (b.y - a.y)) * (b.x - a.x);
    assert.ok(xAt > 3 - 1e-9 && xAt < 4 + 1e-9, `top-wall crossing at x=${xAt} must be in the doorway`);
  }
}

// --- PROOF on many random, fully-connected maps -----------------------------
// Every cell centre must be routable from every other, and no route may cross a
// wall. generateFloorWalls() guarantees connectivity, so this must always hold.
const cellCentres = [];
for (let cy = 0; cy < GRID.rows; cy++) {
  for (let cx = 0; cx < GRID.cols; cx++) cellCentres.push({ x: cx + 0.5, y: cy + 0.5 });
}
let routesChecked = 0;
for (let seed = 1; seed <= 40; seed++) {
  const walls = generateFloorWalls(mulberry32(seed));
  const start = cellCentres[0];
  for (const goal of cellCentres) {
    const r = findRoute(start, goal, walls);
    assert.ok(r.reachable, `seed ${seed}: ${JSON.stringify(goal)} should be reachable (connected map)`);
    assert.ok(pathClearsWalls(r.path, walls), `seed ${seed}: route to ${JSON.stringify(goal)} crosses a wall`);
    routesChecked++;
  }
}

console.log(`gridRouting.test.mjs: all assertions passed (${routesChecked} random-map routes verified)`);
