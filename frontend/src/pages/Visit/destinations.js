import {
  perimeterWalls,
  horizontalEdgeKey,
  verticalEdgeKey,
} from '../../components/GridFloorPlan/gridModel';
import { generateFloorWalls } from '../../components/GridFloorPlan/floorGen';

// The institution a visitor has just walked into (would come from the QR code's
// building/floor id in a real deployment).
export const VENUE = {
  name: 'Science Building',
  floorLabel: 'Ground Floor',
};

// Destination POIs, in the SAME grid coordinate space as the KNN model and the
// floor editor (x ∈ [0,7], y ∈ [0,5], 1 cell ≈ 1 m). Each sits on a distinct
// CELL CENTRE (x.5, y.5): off every wall line, so the router can always reach
// it cleanly whatever walls the layout generator produces.
export const DESTINATIONS = [
  { id: 'reception', label: 'Reception', category: 'help', icon: '🛎️', x: 0.5, y: 0.5 },
  { id: 'cafe', label: 'Café', category: 'food', icon: '☕', x: 6.5, y: 0.5 },
  { id: 'lecture-101', label: 'Lecture Hall 101', category: 'rooms', icon: '🎓', x: 0.5, y: 4.5 },
  { id: 'lab-a', label: 'Lab A', category: 'rooms', icon: '🔬', x: 6.5, y: 4.5 },
  { id: 'restrooms', label: 'Restrooms', category: 'facilities', icon: '🚻', x: 3.5, y: 0.5 },
  // The building's vertical-circulation core: stairs and lift sit side by side.
  { id: 'elevator', label: 'Elevator', category: 'facilities', icon: '🛗', x: 2.5, y: 4.5 },
  { id: 'stairs', label: 'Stairs', category: 'facilities', icon: '🪜', x: 4.5, y: 4.5 },
  { id: 'exit', label: 'Main Exit', category: 'exits', icon: '🚪', x: 3.5, y: 4.5 },
];

// Fixed map landmarks drawn on the floor at all times (not just when selected),
// so the stairs and lift read as real fixtures. They double as destinations.
export const FLOOR_FEATURES = DESTINATIONS.filter(
  (d) => d.id === 'elevator' || d.id === 'stairs',
);

export const CATEGORIES = [
  { id: 'all', label: 'All' },
  { id: 'rooms', label: 'Rooms' },
  { id: 'facilities', label: 'Facilities' },
  { id: 'food', label: 'Food' },
  { id: 'help', label: 'Help' },
  { id: 'exits', label: 'Exits' },
];

// The follow-up question after "Where do you want to go?".
export const ROUTE_PREFERENCES = [
  { id: 'fastest', label: 'Fastest route', icon: '⚡', hint: 'Shortest path' },
  { id: 'step-free', label: 'Step-free', icon: '♿', hint: 'Avoid stairs' },
  { id: 'quiet', label: 'Avoid crowds', icon: '🤫', hint: 'Quieter corridors' },
];

// A fresh, COMPLEX floor layout for each visit — rooms, corridors and doorways
// generated at random but guaranteed fully connected, so every destination
// stays reachable and the router has real walls to work around. Call once per
// session (see Visit.jsx) so the map is stable while the visitor navigates.
export function generateVenueWalls() {
  return generateFloorWalls();
}

// A fixed, hand-drawn layout (perimeter + a service-core room with a doorway).
// Kept as a simpler, deterministic alternative to the random generator above.
export function visitorWalls() {
  const walls = perimeterWalls();
  // The lower-middle service core: walls on three sides (the fourth is the
  // building's bottom wall), with a DOORWAY left open in the top wall at the
  // x=3..4 segment so visitors can actually walk into the stairs/lift lobby.
  [2, 4].forEach((x) => walls.add(horizontalEdgeKey(x, 3))); // top wall, gap at x=3..4
  [3, 4].forEach((y) => walls.add(verticalEdgeKey(2, y))); // left wall
  [3, 4].forEach((y) => walls.add(verticalEdgeKey(5, y))); // right wall
  return walls;
}
