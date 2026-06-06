# RmFindr Hackathon Deliverables

## Core Thesis

**GPS stops at the front door. RmFindr keeps going by treating messy indoor Wi-Fi signals as location fingerprints.**

Everything should ladder back to that idea. The project is strongest when judges see a real positioning loop instead of only hearing about indoor navigation.

## Recommended Deliverable Roles

### 1. Demo Video

Job: prove the prototype works.

Lead with the moving dot and floor plan as early as possible. The viewer should understand within 20 seconds that this is an indoor positioning system using ordinary Wi-Fi signals.

### 2. Technical Walkthrough Video

Job: prove the prototype is credible.

This should not repeat the pitch. It should explain the hardware setup, calibration data, estimator, backend stream, and dashboard state flow.

### 3. Slides

Job: make the story easy for judges to remember.

The deck should connect problem, insight, prototype, architecture, and future value. Keep it proof-heavy: floor plan, signal readings, calibration points, live trail, and architecture diagram.

## Best Narrative

1. Dense buildings create the hardest navigation problems after GPS has already gotten you to the door.
2. Beacon-based indoor positioning is useful, but expensive to install and maintain.
3. RmFindr asks whether existing Wi-Fi signals can become the indoor positioning layer.
4. Instead of fighting indoor signal distortion, RmFindr uses it as the fingerprint.
5. The hackathon prototype maps a room once, scans live RSSI values, estimates position, and visualizes movement.
6. The same idea could become QR-launched indoor maps and anonymous building movement analytics.

## Tone

Use concrete, judge-friendly language:

- "Wi-Fi fingerprint" instead of "multipath model" unless the technical video needs detail.
- "Map once, locate live" as the simple workflow.
- "Data over geometry" as the technical insight.
- "Low-cost indoor positioning without dedicated beacons" as the value proposition.

Avoid making the prototype sound more production-ready than it is. The credibility comes from being honest about scope while showing a complete loop.

## Immediate Team Tasks

1. Capture a 10-15 second screen recording of the dashboard showing the live position dot moving.
2. Capture a calibration clip where someone clicks known points and saves Wi-Fi readings.
3. Take one photo or short clip of the three phone hotspots placed around the room.
4. Save a screenshot of the final floor plan with anchors, calibration points, and trail.
5. Record a clean architecture diagram or use the README Mermaid diagram as the basis for slides.
6. Keep one example calibration JSON object and one live RSSI reading for the technical walkthrough.

