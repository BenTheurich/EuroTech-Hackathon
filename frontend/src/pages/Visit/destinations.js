import {
  perimeterWalls,
  horizontalEdgeKey,
  verticalEdgeKey,
} from '../../components/GridFloorPlan/gridModel';

// The institution a visitor has just walked into (would come from the QR code's
// building/floor id in a real deployment).
export const VENUE = {
  name: 'Science Building',
  floorLabel: 'Ground Floor',
};

// Destination POIs, in the SAME grid coordinate space as the KNN model and the
// floor editor (x ∈ [0,7], y ∈ [0,5], 1 cell ≈ 1 m).
export const DESTINATIONS = [
  { id: 'reception', label: 'Reception', category: 'help', icon: '🛎️', x: 0.6, y: 0.6 },
  { id: 'cafe', label: 'Café', category: 'food', icon: '☕', x: 6.4, y: 0.6 },
  { id: 'lecture-101', label: 'Lecture Hall 101', category: 'rooms', icon: '🎓', x: 1, y: 4.4 },
  { id: 'lab-a', label: 'Lab A', category: 'rooms', icon: '🔬', x: 6.4, y: 4.4 },
  { id: 'restrooms', label: 'Restrooms', category: 'facilities', icon: '🚻', x: 3.5, y: 0.5 },
  { id: 'lifts', label: 'Lifts & Stairs', category: 'facilities', icon: '🛗', x: 3.5, y: 2.5 },
  { id: 'exit', label: 'Main Exit', category: 'exits', icon: '🚪', x: 3.5, y: 4.5 },
];

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

// A fixed, read-only floor layout shown to visitors (perimeter + a few interior
// walls so the space reads like a real plan). Not editable on the visitor side.
export function visitorWalls() {
  const walls = perimeterWalls();
  // Two interior partitions splitting the lower half into rooms.
  [2, 3, 4].forEach((x) => walls.add(horizontalEdgeKey(x, 3)));
  [3, 4].forEach((y) => walls.add(verticalEdgeKey(2, y)));
  [3, 4].forEach((y) => walls.add(verticalEdgeKey(5, y)));
  return walls;
}
