"""
Prerecorded SMOOTH walk around the reception floor — for the demo video.

Unlike simulate_walk.py (which fakes RSSI and runs it through the KNN model),
this plays a hand-authored path straight onto the map. We do that on purpose:
the KNN + tracker pipeline is built to *denoise real, noisy* localization, so
feeding it a clean path gives jerky, lagging output. For a "look how it walks
the building" demo we want the dot to glide exactly along an authored route.

The path is a closed loop that tours the reception floor's points of interest,
threads the service-core doorway, and NEVER crosses a wall (verified on start
against the same wall layout the visitor map draws — pathfinding.default_walls /
destinations.js visitorWalls). Because the loop ends where it starts, it repeats
seamlessly.

What it demonstrates: open /visit, pick a destination, and the blue Dijkstra
route re-plans around the walls as the dot walks — wall-aware routing, live.

Run (backend must be up):

    python scanner/simulate_reception_walk.py
    python scanner/simulate_reception_walk.py --loop-seconds 30 --fps 20
    python scanner/simulate_reception_walk.py --once     # one lap, then stop

Requires only `requests`.
"""

import argparse
import math
import time

import requests


DEFAULT_BACKEND_URL = "http://localhost:8000/api/playback"

# Reception floor: 7 x 5 m grid (x 0..7, y 0..5), 1 cell ~= 1 m. The service
# core (stairs/lift lobby) sits at cells x2..5, y3..5 with a single doorway in
# its top wall at x=3..4. POIs: reception (0.5,0.5), restrooms (3.5,0.5),
# cafe (6.5,0.5), lab A (6.5,4.5), stairs (4.5,4.5), lift (2.5,4.5),
# lecture hall (0.5,4.5).
#
# A leisurely loop that visits them all and threads the doorway in and back out.
# Every consecutive pair has clear line of sight (asserted at startup), so we can
# just interpolate straight between them.
WAYPOINTS = [
    (0.5, 0.5),   # Reception (start / end)
    (3.5, 0.5),   # Restrooms
    (6.5, 0.5),   # Cafe
    (6.5, 2.5),   # down the right side
    (6.5, 4.5),   # Lab A
    (6.5, 2.2),   # back up into the open area (above the core wall)
    (3.5, 2.2),   # line up with the doorway
    (4.5, 4.5),   # in through the doorway -> Stairs
    (2.5, 4.5),   # Lift
    (3.5, 2.2),   # back out through the doorway
    (0.7, 2.2),   # across to the left strip
    (0.5, 4.5),   # Lecture Hall
    (0.5, 2.0),   # back up the left side
    (0.5, 0.5),   # home to Reception (loop closes)
]


# ---------------------------------------------------------------------------
# Wall layout + line-of-sight check (a self-contained mirror of
# backend/pathfinding.default_walls + line_of_sight_clear, so this script can
# verify its own path without importing the backend).
# ---------------------------------------------------------------------------
GRID_COLS, GRID_ROWS = 7, 5
_EPS = 1e-9


def _reception_walls():
    walls = set()
    for x in range(GRID_COLS):
        walls.add(f"h-{x}-0")
        walls.add(f"h-{x}-{GRID_ROWS}")
    for y in range(GRID_ROWS):
        walls.add(f"v-0-{y}")
        walls.add(f"v-{GRID_COLS}-{y}")
    for x in (2, 4):  # core top wall, doorway gap at x=3..4
        walls.add(f"h-{x}-3")
    for y in (3, 4):
        walls.add(f"v-2-{y}")
        walls.add(f"v-5-{y}")
    return walls


def _line_of_sight_clear(ax, ay, bx, by, walls):
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return True
    step_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
    step_y = 1 if dy > 0 else (-1 if dy < 0 else 0)
    cx = min(GRID_COLS - 1, max(0, math.floor(ax)))
    cy = min(GRID_ROWS - 1, max(0, math.floor(ay)))
    t_max_x = ((cx + 1 if step_x > 0 else cx) - ax) / dx if step_x else math.inf
    t_max_y = ((cy + 1 if step_y > 0 else cy) - ay) / dy if step_y else math.inf
    t_delta_x = abs(1 / dx) if step_x else math.inf
    t_delta_y = abs(1 / dy) if step_y else math.inf
    while t_max_x <= 1 + _EPS or t_max_y <= 1 + _EPS:
        if abs(t_max_x - t_max_y) < _EPS:
            x_line = cx + 1 if step_x > 0 else cx
            y_line = cy + 1 if step_y > 0 else cy
            dcx, dcy = cx + step_x, cy + step_y
            via_x = f"v-{x_line}-{cy}" not in walls and f"h-{dcx}-{y_line}" not in walls
            via_y = f"h-{cx}-{y_line}" not in walls and f"v-{x_line}-{dcy}" not in walls
            if not via_x and not via_y:
                return False
            cx, cy = dcx, dcy
            t_max_x += t_delta_x
            t_max_y += t_delta_y
        elif t_max_x < t_max_y:
            wall = f"v-{cx + 1}-{cy}" if step_x > 0 else f"v-{cx}-{cy}"
            if wall in walls:
                return False
            cx += step_x
            t_max_x += t_delta_x
        else:
            wall = f"h-{cx}-{cy + 1}" if step_y > 0 else f"h-{cx}-{cy}"
            if wall in walls:
                return False
            cy += step_y
            t_max_y += t_delta_y
    return True


def verify_path(waypoints):
    """Fail loudly if any leg crosses a wall, so an edited route can't ship broken."""
    walls = _reception_walls()
    bad = [
        (a, b)
        for a, b in zip(waypoints, waypoints[1:])
        if not _line_of_sight_clear(a[0], a[1], b[0], b[1], walls)
    ]
    if bad:
        raise SystemExit(
            "Walk path crosses a wall on these legs (fix WAYPOINTS):\n  "
            + "\n  ".join(f"{a} -> {b}" for a, b in bad)
        )
    if waypoints[0] != waypoints[-1]:
        raise SystemExit("Walk does not loop: first waypoint must equal the last.")


def path_length(waypoints):
    return sum(
        math.hypot(b[0] - a[0], b[1] - a[1])
        for a, b in zip(waypoints, waypoints[1:])
    )


def positions(waypoints, step):
    """Yield evenly spaced points along the loop (excludes the duplicate end)."""
    for a, b in zip(waypoints, waypoints[1:]):
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        if seg == 0:
            continue
        count = max(1, int(round(seg / step)))
        for i in range(count):
            t = i / count
            yield (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Smooth prerecorded reception-floor walk.")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--loop-seconds", type=float, default=45.0,
                        help="Seconds for one full lap of the building.")
    parser.add_argument("--fps", type=float, default=15.0,
                        help="Position updates per second (the frontend smooths between them).")
    parser.add_argument("--once", action="store_true", help="Walk a single lap, then stop.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    verify_path(WAYPOINTS)

    length = path_length(WAYPOINTS)
    dt = 1.0 / args.fps
    speed = length / args.loop_seconds          # metres per second
    step = speed * dt                            # metres between updates
    frame = list(positions(WAYPOINTS, step))

    print("Smooth reception-floor walk.")
    print(f"  POST -> {args.backend_url}")
    print(f"  loop {length:.1f} m in {args.loop_seconds:.0f} s "
          f"(~{speed:.2f} m/s), {len(frame)} points/lap at {args.fps:.0f} fps")
    print("  Open /visit, pick a destination, and watch the route re-plan. CTRL+C to stop.\n")

    session = requests.Session()
    lap = 0
    while True:
        lap += 1
        for (x, y) in frame:
            try:
                session.post(args.backend_url, json={"x": round(x, 3), "y": round(y, 3)}, timeout=2)
            except requests.exceptions.ConnectionError:
                print("Could not reach backend on port 8000. Is it running?")
                time.sleep(2)
                break
            except requests.exceptions.RequestException as error:
                print(f"Request failed: {error}")
            time.sleep(dt)
        if args.once:
            print("Single lap complete.")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nWalk stopped by user.")
