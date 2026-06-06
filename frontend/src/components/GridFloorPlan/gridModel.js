// ============================================================================
// GRID MODEL — the shared geometry/coordinate contract for the floor editor.
//
// Locked to the backend KNN coordinate space: the model (backend/knn_model.py
// + data/*.csv) predicts (x, y) with x ∈ [0, 7], y ∈ [0, 5]. We treat those
// integers as GRID VERTICES, so the floor is an 8 × 6 lattice of points = a
// 7 × 5 grid of cells, with the four Wi-Fi anchors A–D on the corner vertices.
// ============================================================================
export const GRID = { cols: 7, rows: 5 }; // cells; vertices run 0..7 (x), 0..5 (y)

export const ANCHORS = [
  { id: 'A', x: 0, y: 0 },
  { id: 'B', x: GRID.cols, y: 0 },
  { id: 'C', x: 0, y: GRID.rows },
  { id: 'D', x: GRID.cols, y: GRID.rows },
];

// Edge keys: `h-${x}-${y}` is the horizontal segment from (x,y)→(x+1,y);
//            `v-${x}-${y}` is the vertical segment from (x,y)→(x,y+1).
export function horizontalEdgeKey(x, y) {
  return `h-${x}-${y}`;
}

export function verticalEdgeKey(x, y) {
  return `v-${x}-${y}`;
}

// Perimeter wall segments — a sensible starting "room outline" for a new floor.
export function perimeterWalls() {
  const walls = new Set();
  for (let x = 0; x < GRID.cols; x++) {
    walls.add(horizontalEdgeKey(x, 0)); // top
    walls.add(horizontalEdgeKey(x, GRID.rows)); // bottom
  }
  for (let y = 0; y < GRID.rows; y++) {
    walls.add(verticalEdgeKey(0, y)); // left
    walls.add(verticalEdgeKey(GRID.cols, y)); // right
  }
  return walls;
}

// Every possible edge in the lattice (horizontals then verticals).
export function allEdges() {
  const edges = [];
  for (let y = 0; y <= GRID.rows; y++) {
    for (let x = 0; x < GRID.cols; x++) {
      edges.push({ key: horizontalEdgeKey(x, y), x1: x, y1: y, x2: x + 1, y2: y });
    }
  }
  for (let x = 0; x <= GRID.cols; x++) {
    for (let y = 0; y < GRID.rows; y++) {
      edges.push({ key: verticalEdgeKey(x, y), x1: x, y1: y, x2: x, y2: y + 1 });
    }
  }
  return edges;
}
