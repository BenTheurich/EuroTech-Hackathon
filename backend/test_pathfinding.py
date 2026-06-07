import math

from pathfinding import (
    default_walls,
    find_route,
    horizontal_edge_key,
    line_of_sight_clear,
    vertical_edge_key,
)


def _path_clears_walls(path, walls):
    pts = [(p["x"], p["y"]) for p in path]
    return all(
        line_of_sight_clear(pts[i - 1][0], pts[i - 1][1], pts[i][0], pts[i][1], walls)
        for i in range(1, len(pts))
    )


def test_open_floor_is_a_single_straight_segment():
    route = find_route({"x": 0.5, "y": 0.5}, {"x": 6.5, "y": 4.5}, walls=set())
    assert route["reachable"] is True
    assert len(route["path"]) == 2
    assert abs(route["distance"] - math.hypot(6, 4)) < 0.02


def test_wall_blocks_line_of_sight_and_route_bends_around_it():
    wall = {vertical_edge_key(3, 0), vertical_edge_key(3, 1), vertical_edge_key(3, 2)}
    assert line_of_sight_clear(1, 1.5, 5, 1.5, wall) is False
    assert line_of_sight_clear(1, 1.5, 5, 1.5, set()) is True
    bent = find_route({"x": 1, "y": 1.5}, {"x": 5, "y": 1.5}, walls=wall)
    assert bent["reachable"] and len(bent["path"]) > 2
    assert _path_clears_walls(bent["path"], wall)
    assert bent["distance"] > math.hypot(4, 0)


def test_does_not_cut_between_two_walls_at_a_corner():
    # v-3-2 and h-2-3 meet at the vertex (3,3) and pinch the corner.
    pinch = {vertical_edge_key(3, 2), horizontal_edge_key(2, 3)}
    assert line_of_sight_clear(2.5, 2.5, 3.5, 3.5, pinch) is False
    route = find_route({"x": 2.5, "y": 2.5}, {"x": 3.5, "y": 3.5}, walls=pinch)
    assert len(route["path"]) > 2
    assert _path_clears_walls(route["path"], pinch)


def test_single_wall_does_not_block_rounding_its_end():
    assert line_of_sight_clear(2.5, 2.5, 3.5, 3.5, {vertical_edge_key(3, 2)}) is True


def test_default_venue_routes_clear_the_walls():
    walls = default_walls()
    route = find_route({"x": 0.5, "y": 0.5}, {"x": 3.5, "y": 4.5}, walls=walls)
    assert route["reachable"] is True
    assert _path_clears_walls(route["path"], walls)


def test_find_route_echoes_preference():
    route = find_route({"x": 1, "y": 1}, {"x": 2, "y": 2}, walls=set(), preference="step-free")
    assert route["preference"] == "step-free"
