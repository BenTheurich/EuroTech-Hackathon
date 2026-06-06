# RmFindr Capture Checklist

## Must-Have Demo Footage

- Dashboard screen recording showing live dot movement.
- Calibration screen recording showing at least three saved points.
- Photo or short clip of three phone hotspot anchors in the room.
- Clip of the laptop moving from one known point to another.
- Final dashboard screenshot with anchors, calibration points, trail, and confidence/status visible.

## Must-Have Technical Assets

- One calibration JSON example.
- One live RSSI reading example.
- Architecture diagram exported from README Mermaid or rebuilt for slides.
- Screenshot of FastAPI route docs or backend terminal if visually useful.
- Screenshot or clip of WebSocket/live updates if the dashboard makes this visible.

## Nice-To-Have Assets

- A simple floor plan image used by the dashboard.
- Side-by-side shot: physical room location and dashboard estimated point.
- Before/after comparison: no indoor GPS vs RmFindr indoor map.
- A quick accuracy sanity check: stand at known point, show estimated point nearby.

## Recording Order

1. Record the dashboard during a successful live tracking run.
2. Record calibration from a clean reset.
3. Record physical setup footage.
4. Capture still screenshots after the best run.
5. Record voiceover last, once the final clips are selected.

## Risk Controls

- If live tracking is inconsistent, show the calibration map and the best successful tracking path.
- If the physical room is visually cluttered, lean on dashboard footage and close-up anchor labels.
- If RSSI values fluctuate, frame it honestly as a hackathon prototype and emphasize the learned fingerprint loop.
- If the UI is not polished yet, keep shots tight on the map, anchor markers, signal readings, and movement trail.

