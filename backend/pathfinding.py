"""Any-angle shortest-path routing that never crosses or corner-cuts a wall.

Backend counterpart of ``frontend/src/components/GridFloorPlan/gridRouting.js``
(identical semantics). Server-side API behind ``POST /api/route``; the visitor
map itself routes client-side for instant reactivity.

Coordinate contract (see ``frontend/.../gridModel.js`` and ``docs/INTEGRATION.md``):

  * The floor is an 8 x 6 lattice of vertices: ``x in 0..7``, ``y in 0..5``
    (= a 7 x 5 grid of cells, 1 cell ~= 1 m). The four Wi-Fi anchors A-D sit on
    the corner vertices.
  * WALLS are impassable segments on the lattice edges (the same ``h-x-y`` /
    ``v-x-y`` keys the editor draws). Cell (cx, cy) is the square
    ``[cx, cx+1] x [cy, cy+1]``; crossing the line x=k between rows hits wall
    ``v-k-row`` and crossing y=m between cols hits wall ``h-col-m``.

A route must not cross a wall, and must not squeeze diagonally between two walls
that meet at a corner. We march a straight line cell-by-cell to test line of
sight (rejecting corner cuts), then run Dijkstra over a visibility graph of the
cell centres (+ the real start and goal). On open floor the start sees the goal
directly, so the route is a single straight segment.
"""

import heapq
import math

# Grid geometry — must stay in lock-step with gridModel.js.
GRID_COLS = 7
GRID_ROWS = 5

_EPS = 1e-9


# ---------------------------------------------------------------------------
# Edge / wall helpers (mirror gridModel.js so keys match what the frontend draws)
# ---------------------------------------------------------------------------
def horizontal_edge_key(x, y):
    return f"h-{x}-{y}"


def vertical_edge_key(x, y):
    return f"v-{x}-{y}"


def default_walls(cols=GRID_COLS, rows=GRID_ROWS):
    """A simple hand-drawn layout: perimeter + a service-core room with a doorway."""
    walls = set()
    for x in range(cols):
        walls.add(horizontal_edge_key(x, 0))
        walls.add(horizontal_edge_key(x, rows))
    for y in range(rows):
        walls.add(vertical_edge_key(0, y))
        walls.add(vertical_edge_key(cols, y))
    for x in (2, 4):  # top wall of the core, doorway gap at x=3..4
        walls.add(horizontal_edge_key(x, 3))
    for y in (3, 4):
        walls.add(vertical_edge_key(2, y))
        walls.add(vertical_edge_key(5, y))
    return walls


# ---------------------------------------------------------------------------
# Line of sight: DDA grid march that respects edge walls and forbids corner cuts
# ---------------------------------------------------------------------------
def line_of_sight_clear(ax, ay, bx, by, walls, cols=GRID_COLS, rows=GRID_ROWS):
    dx = bx - ax
    dy = by - ay
    if dx == 0 and dy == 0:
        return True

    step_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
    step_y = 1 if dy > 0 else (-1 if dy < 0 else 0)

    cx = min(cols - 1, max(0, math.floor(ax)))
    cy = min(rows - 1, max(0, math.floor(ay)))

    next_x_line = cx + 1 if step_x > 0 else cx
    next_y_line = cy + 1 if step_y > 0 else cy
    t_max_x = (next_x_line - ax) / dx if step_x != 0 else math.inf
    t_max_y = (next_y_line - ay) / dy if step_y != 0 else math.inf
    t_delta_x = abs(1 / dx) if step_x != 0 else math.inf
    t_delta_y = abs(1 / dy) if step_y != 0 else math.inf

    while t_max_x <= 1 + _EPS or t_max_y <= 1 + _EPS:
        if abs(t_max_x - t_max_y) < _EPS:
            # Diagonal vertex crossing: allowed only if one L-detour around the
            # vertex is fully open, else it would cut a wall corner.
            x_line = cx + 1 if step_x > 0 else cx
            y_line = cy + 1 if step_y > 0 else cy
            dest_cx = cx + step_x
            dest_cy = cy + step_y
            via_x = (
                vertical_edge_key(x_line, cy) not in walls
                and horizontal_edge_key(dest_cx, y_line) not in walls
            )
            via_y = (
                horizontal_edge_key(cx, y_line) not in walls
                and vertical_edge_key(x_line, dest_cy) not in walls
            )
            if not via_x and not via_y:
                return False
            cx, cy = dest_cx, dest_cy
            t_max_x += t_delta_x
            t_max_y += t_delta_y
        elif t_max_x < t_max_y:
            v_wall = vertical_edge_key(cx + 1, cy) if step_x > 0 else vertical_edge_key(cx, cy)
            if v_wall in walls:
                return False
            cx += step_x
            t_max_x += t_delta_x
        else:
            h_wall = horizontal_edge_key(cx, cy + 1) if step_y > 0 else horizontal_edge_key(cx, cy)
            if h_wall in walls:
                return False
            cy += step_y
            t_max_y += t_delta_y
    return True


def _polyline_length(points):
    return sum(
        math.hypot(x2 - x1, y2 - y1)
        for (x1, y1), (x2, y2) in zip(points, points[1:])
    )


# ---------------------------------------------------------------------------
# Public entry point used by the API
# ---------------------------------------------------------------------------
def find_route(start, goal, walls=None, preference="fastest", cols=GRID_COLS, rows=GRID_ROWS):
    """Shortest-path route from the user's location to their destination.

    Straight where the floor is open, turning only where a wall blocks the way,
    never crossing a wall or cutting a corner. Falls back to a direct segment
    (``reachable: False``) if the destination is walled off entirely.
    """
    wall_set = set(walls) if walls is not None else default_walls()

    start_pt = (float(start["x"]), float(start["y"]))
    goal_pt = (float(goal["x"]), float(goal["y"]))

    # Nodes: start (0), goal (1), then every cell centre (off all wall lines).
    nodes = [start_pt, goal_pt]
    for cy in range(rows):
        for cx in range(cols):
            nodes.append((cx + 0.5, cy + 0.5))

    n = len(nodes)
    dist = [math.inf] * n
    prev = [-1] * n
    done = [False] * n
    dist[0] = 0.0
    heap = [(0.0, 0)]

    while heap:
        d, u = heapq.heappop(heap)
        if done[u]:
            continue
        done[u] = True
        if u == 1:
            break
        ux, uy = nodes[u]
        for v in range(n):
            if done[v] or v == u:
                continue
            vx, vy = nodes[v]
            if not line_of_sight_clear(ux, uy, vx, vy, wall_set, cols, rows):
                continue
            w = math.hypot(vx - ux, vy - uy)
            if d + w < dist[v]:
                dist[v] = d + w
                prev[v] = u
                heapq.heappush(heap, (dist[v], v))

    reachable = dist[1] < math.inf
    if reachable:
        path_nodes = []
        k = 1
        while k != -1:
            path_nodes.append(nodes[k])
            k = prev[k]
        path_nodes.reverse()
    else:
        path_nodes = [start_pt, goal_pt]

    return {
        "reachable": reachable,
        "preference": preference,
        "path": [{"x": x, "y": y} for x, y in path_nodes],
        "distance": round(_polyline_length(path_nodes), 2),
    }
