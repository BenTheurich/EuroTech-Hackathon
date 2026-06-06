# RmFindr 2-Minute Technical Walkthrough Script

## Purpose

Explain why the prototype is technically credible and how the parts fit together.

## Structure

### 0:00-0:12 - Technical Thesis

Visual: architecture diagram or dashboard with signal values.

Voiceover:
"RmFindr is an indoor positioning prototype based on Wi-Fi fingerprinting. Instead of calculating distance from signal strength, it learns the signal pattern at known locations."

### 0:12-0:30 - Hardware Inputs

Visual: three phone hotspots and laptop scanner.

Voiceover:
"The hackathon setup uses three phone hotspots as fixed anchors. The laptop acts as the moving scanner and reads RSSI values from each anchor."

Mention:
- Anchor A, B, C
- Known anchor placement
- Laptop as scanner

### 0:30-0:52 - Calibration Data

Visual: calibration click on floor plan plus JSON snippet.

Voiceover:
"In calibration mode, the user clicks a known point on the floor plan. RmFindr stores the x-y coordinate with the current RSSI readings."

Example:
```json
{
  "x": 42,
  "y": 68,
  "signals": {
    "anchor_a": -51,
    "anchor_b": -67,
    "anchor_c": -74
  }
}
```

### 0:52-1:16 - Estimator

Visual: simple diagram of live signal vector compared against saved fingerprints.

Voiceover:
"For live tracking, the backend compares the current signal vector to the calibration fingerprints. A nearest-neighbor style estimator chooses the closest matching fingerprint and returns an estimated x-y position."

Optional line if the implementation uses it:
"Scikit-learn gives us a clean path to extend this from nearest neighbor to k-nearest neighbors or regression models."

### 1:16-1:38 - Backend And Stream

Visual: README architecture diagram.

Voiceover:
"FastAPI stores calibration points, receives scan updates, runs the estimator, and streams position updates over WebSocket. The dashboard subscribes to those updates so the map changes live."

Architecture labels:
- Phone hotspot anchors
- Python Wi-Fi scanner
- FastAPI backend
- Position estimator
- WebSocket stream
- React indoor map

### 1:38-1:52 - Dashboard State

Visual: React dashboard with anchors, calibration points, trail, and confidence/status indicator.

Voiceover:
"The dashboard shows both the inputs and the result: anchor locations, saved fingerprints, live RSSI readings, estimated position, recent movement trail, and confidence."

### 1:52-2:00 - Future Technical Direction

Visual: final architecture or roadmap slide.

Voiceover:
"Next steps are better floor handling, more calibration density, confidence scoring, phone-based scanning, and privacy-preserving aggregate analytics for building operators."

## Technical Walkthrough Rules

- Do not re-pitch the problem for more than 12 seconds.
- Use one concrete calibration example.
- Show the architecture diagram once and the live dashboard once.
- Be honest that this is a hackathon prototype, not production GPS.
- End with plausible next engineering steps, not vague scale claims.

