// ============================================================================
// FLOOR GENERATOR — build a complex, fully-connected floor layout.
//
// Produces a wall set (perimeter + interior partitions) that is guaranteed
// CONNECTED: every cell is reachable from every other, so every destination
// stays routable no matter how the walls fall. That lets us hand the router a
// fresh, non-trivial map each session to prove it really respects walls.
//
// Method: a randomized-DFS maze (perfect spanning tree → connected by
// construction), then "braiding" — randomly removing a fraction of the
// remaining interior walls. Removing walls only adds connections, so the result
// stays connected while looking more like rooms-and-corridors than a tight maze.
// ============================================================================
import { GRID, horizontalEdgeKey, verticalEdgeKey, perimeterWalls } from './gridModel.js';

// The shared wall between two edge-adjacent cells:
//   left|right cells (cx,cy)|(cx+1,cy) → vertical wall on line x=cx+1
const wallBetweenLR = (cx, cy) => verticalEdgeKey(cx + 1, cy);
//   top|bottom cells (cx,cy)|(cx,cy+1) → horizontal wall on line y=cy+1
const wallBetweenTB = (cx, cy) => horizontalEdgeKey(cx, cy + 1);

/**
 * Generate a connected floor layout.
 *
 * @param {() => number} [rand]   RNG returning [0,1) (defaults to Math.random)
 * @param {number} [braid]        fraction of leftover interior walls to remove
 *                                (0 = tight maze, 1 = wide open). Default 0.5.
 * @returns {Set<string>} wall edge keys (perimeter included)
 */
export function generateFloorWalls(rand = Math.random, braid = 0.5) {
  const { cols, rows } = GRID;

  // Start with every interior separation present (each cell boxed in).
  const interior = new Set();
  for (let cy = 0; cy < rows; cy++) {
    for (let cx = 0; cx < cols; cx++) {
      if (cx + 1 < cols) interior.add(wallBetweenLR(cx, cy));
      if (cy + 1 < rows) interior.add(wallBetweenTB(cx, cy));
    }
  }

  // Randomized-DFS carve: remove walls to build a spanning tree over all cells.
  const key = (cx, cy) => `${cx},${cy}`;
  const visited = new Set();
  const startCx = Math.floor(rand() * cols);
  const startCy = Math.floor(rand() * rows);
  const stack = [[startCx, startCy]];
  visited.add(key(startCx, startCy));

  while (stack.length) {
    const [cx, cy] = stack[stack.length - 1];
    const neighbours = [];
    if (cx + 1 < cols && !visited.has(key(cx + 1, cy))) neighbours.push(['R', cx + 1, cy]);
    if (cx - 1 >= 0 && !visited.has(key(cx - 1, cy))) neighbours.push(['L', cx - 1, cy]);
    if (cy + 1 < rows && !visited.has(key(cx, cy + 1))) neighbours.push(['D', cx, cy + 1]);
    if (cy - 1 >= 0 && !visited.has(key(cx, cy - 1))) neighbours.push(['U', cx, cy - 1]);

    if (neighbours.length === 0) {
      stack.pop();
      continue;
    }
    const [dir, nx, ny] = neighbours[Math.floor(rand() * neighbours.length)];
    if (dir === 'R') interior.delete(wallBetweenLR(cx, cy));
    else if (dir === 'L') interior.delete(wallBetweenLR(nx, ny));
    else if (dir === 'D') interior.delete(wallBetweenTB(cx, cy));
    else interior.delete(wallBetweenTB(nx, ny));
    visited.add(key(nx, ny));
    stack.push([nx, ny]);
  }

  // Braid: open the maze up. Removing walls can only keep it connected.
  if (braid > 0) {
    for (const w of [...interior]) {
      if (rand() < braid) interior.delete(w);
    }
  }

  const walls = perimeterWalls();
  for (const w of interior) walls.add(w);
  return walls;
}
