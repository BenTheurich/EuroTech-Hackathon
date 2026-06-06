# RmFindr Slide Outline

## Recommended Deck Length

Use 6 core slides plus 1 optional backup slide. This is enough for a concise hackathon pitch without burying the demo.

## Slide 1 - RmFindr

Claim:
GPS stops at the front door. RmFindr keeps going.

Proof object:
Dashboard screenshot with floor plan, anchors, calibration points, and live dot.

Speaker note:
"RmFindr is a low-cost indoor positioning prototype using Wi-Fi fingerprints. We map a space once, read live signal patterns, and estimate where the device is indoors."

## Slide 2 - The Problem

Claim:
The hardest navigation problems often happen after you arrive at the building.

Proof object:
Compact visual list: mall shop, airport gate, clinic room, lecture hall, office suite, train platform.

Speaker note:
"Dense buildings are vertical, crowded, and signal-blocked. GPS does not reliably tell you which corridor, floor, room, or platform you need."

## Slide 3 - The Insight

Claim:
Indoor signal distortion is not only noise. It can be a fingerprint.

Proof object:
Three mini signal vectors from different map locations:
- Point 1: A -51, B -67, C -74
- Point 2: A -64, B -55, C -70
- Point 3: A -73, B -62, C -49

Speaker note:
"Traditional triangulation tries to convert signal strength into distance. Indoors, reflections and walls break that geometry. RmFindr takes a data-first approach: the messy pattern itself becomes the location signature."

## Slide 4 - The Demo Loop

Claim:
Map once. Scan live. Estimate position. Visualize movement.

Proof object:
Four-step loop diagram:
1. Place anchors
2. Save calibration fingerprints
3. Compare live RSSI
4. Update map position

Speaker note:
"The prototype demonstrates the full loop using three phone hotspots, a laptop scanner, a FastAPI backend, and a React dashboard."

## Slide 5 - System Architecture

Claim:
RmFindr turns Wi-Fi readings into a live indoor map position.

Proof object:
Architecture diagram:
Phone Hotspot Anchors -> Python Wi-Fi Scanner -> FastAPI Backend -> Position Estimator -> WebSocket Stream -> React Indoor Map

Speaker note:
"The scanner collects RSSI readings, the backend stores calibration fingerprints and estimates position, and the WebSocket stream keeps the dashboard updated in real time."

## Slide 6 - Why It Matters

Claim:
Low-cost indoor positioning can become a navigation and spatial intelligence layer for buildings.

Proof object:
Two-column value frame:
- Visitors: find rooms, shops, gates, platforms, offices
- Operators: understand anonymous flow, confusing routes, dead zones, signage needs

Speaker note:
"A production version could be launched from QR codes at entrances, elevators, and major junctions. Visitors get indoor wayfinding, while operators learn where navigation breaks down using aggregated, privacy-conscious analytics."

## Optional Backup Slide - Hackathon Scope And Next Steps

Claim:
The prototype proves the loop; production would improve accuracy, privacy, and deployment.

Proof object:
Three sections:
- Built: calibration, scanning, estimator, dashboard
- Next: denser map, confidence scoring, multi-floor handling, mobile scanning
- Production: opt-in sessions, short-lived IDs, aggregate analytics

Speaker note:
"We are not claiming production-grade GPS. We are showing that ordinary Wi-Fi patterns can support a practical indoor positioning workflow."

## Design Direction

- Visual system: clean technical map interface, not a generic startup pitch deck.
- Palette: white or dark-neutral base with high-contrast anchor colors for A, B, and C.
- Repeated motif: signal vectors becoming points on a map.
- Best hero visual: the actual dashboard, even if rough.
- Avoid: stock city photos, too many feature cards, long paragraphs, exaggerated accuracy claims.

