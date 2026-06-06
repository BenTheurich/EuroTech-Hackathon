# RmFindr

**Spatial Intelligence and Indoor Tracking via Wi-Fi Fingerprinting.**

![Hackathon Status](https://img.shields.io/badge/Status-Hackathon_Prototype-orange)
![Tech Stack](https://img.shields.io/badge/Stack-React%20%7C%20FastAPI%20%7C%20Scikit--Learn-blue)
![License](https://img.shields.io/badge/License-MIT-green)

> **GPS stops at the front door. RmFindr keeps going.**

RmFindr is a hackathon prototype for low-cost indoor positioning using Wi-Fi fingerprints. It turns ordinary Wi-Fi signal patterns into an indoor location system for places where GPS fails: malls, airports, hospitals, universities, train stations, clinics, and dense city buildings.

**Map a space once. Read the Wi-Fi signal pattern. Estimate where you are indoors.**

## The Problem

In dense cities like Hong Kong, the hardest navigation problems often happen after you arrive at the building.

Finding the right mall shop, airport gate, train platform, clinic room, lecture hall, or office suite can be confusing because GPS is unreliable indoors. Large buildings are dense, vertical, and full of signal-blocking walls, escalators, corridors, underground spaces, and overlapping floors.

Existing indoor positioning solutions often require dedicated hardware such as Bluetooth beacons, UWB tags, or expensive venue infrastructure.

RmFindr explores a simpler question:

**What if buildings could be mapped using the Wi-Fi signals already around us?**

## Our Solution

Traditional Wi-Fi triangulation tries to calculate distance from signal strength. Indoors, that breaks down quickly. Signals bounce off walls, glass, doors, people, and metal surfaces. This is called multipath fading, and it makes pure geometric positioning unreliable.

RmFindr takes a different approach: **data over geometry.**

Instead of treating indoor signal distortion as noise, we use it as a fingerprint. Every location in a room has a slightly different combination of Wi-Fi signal strengths. By mapping those fingerprints once, we can later compare live readings against the map and estimate where the device is.

This is not GPS. It is indoor positioning through learned signal patterns.

## Core Demo

For the 24-hour prototype:

- Three phones act as fixed Wi-Fi anchors using personal hotspots.
- The anchors are placed around the room at known positions.
- A laptop acts as the moving scanner.
- The laptop reads RSSI signal strengths from the hotspot anchors.
- A FastAPI backend estimates the laptop's position.
- A React dashboard displays the result on a 2D indoor map.

The demo shows the full positioning loop:

1. Calibrate the room.
2. Scan live Wi-Fi signals.
3. Estimate the current position.
4. Visualize movement on the map.

## How It Works

### Calibration Mode

Before live tracking, RmFindr builds a fingerprint map.

The user clicks known points on the floor plan. At each point, the system saves the current Wi-Fi signal pattern from the three anchors.

Each calibration point connects a physical location with a signal fingerprint:

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

### Live Tracking Mode

During live tracking, the laptop continuously scans Wi-Fi signal strengths.

The backend compares the live signal pattern against the saved calibration fingerprints using a nearest-neighbor style estimator. The dashboard updates the estimated position as a moving dot on the indoor map.

## Dashboard

The React dashboard makes the positioning process visible at a glance:

- Fixed Wi-Fi anchor locations
- Saved calibration points
- Live RSSI readings
- Estimated current position
- Recent movement trail
- Confidence/status indicator

Judges can see the inputs, the learned fingerprint map, and the estimated position update in real time.

## System Architecture

```mermaid
flowchart LR
    A[Phone Hotspot Anchors] --> B[Python Wi-Fi Scanner]
    B --> C[FastAPI Backend]
    C --> D[Position Estimator]
    D --> E[WebSocket Stream]
    E --> F[React Indoor Map]
```

1. **The Anchors:** Three phone hotspots provide stable Wi-Fi reference signals.
2. **The Scout:** A Python scanner reads nearby Wi-Fi RSSI values from the laptop.
3. **The Brain:** A FastAPI backend stores calibration fingerprints and estimates position.
4. **The Pulse:** WebSocket updates stream live position data to the dashboard.
5. **The Map:** A React interface renders anchors, fingerprints, live readings, movement trail, and position.

## Vision

RmFindr is a prototype for indoor navigation in dense, high-friction environments:

- Find a doctor's office inside a hospital.
- Navigate a mall without hunting for directory screens.
- Locate a train platform or airport gate indoors.
- Guide visitors through university buildings.
- Help venues understand confusing navigation points.
- Enable low-cost indoor positioning without special beacon hardware.

In a city where life happens inside towers, stations, malls, and mixed-use buildings, indoor positioning can become just as important as outdoor maps.

## Business Potential

RmFindr could become a lightweight indoor navigation layer for large public buildings.

A mall, hospital, airport, train station, campus, or office tower could place QR codes at entrances, elevators, reception desks, and major junctions. Visitors scan the code, open the indoor map for that exact building or floor, and get guided to their destination without searching for a directory screen.

For users, the value is simple:

- Find the right shop, gate, platform, clinic room, lecture hall, or office suite.
- Navigate unfamiliar buildings with less stress.
- Use indoor wayfinding where GPS does not work.
- Access the map from a phone, kiosk, or shared display.

For building operators, RmFindr creates a new layer of spatial intelligence:

- Understand anonymous traffic flow through the building.
- Identify confusing routes, dead zones, and navigation pain points.
- See which entrances, corridors, and destinations receive the most movement.
- Improve signage, directory placement, and floor layout.
- Design future buildings around real movement patterns.
- Support tenants, facilities teams, and visitor experience teams with better indoor insights.

A production version would be designed around opt-in sessions, short-lived identifiers, and aggregated analytics, giving buildings useful movement patterns without exposing personal identity.

RmFindr turns indoor navigation from a guessing game into a measurable experience: visitors find their destinations faster, and buildings learn how people actually move through their spaces.

## Hackathon Scope

RmFindr is not production-ready GPS. It is a focused 24-hour prototype showing that Wi-Fi fingerprinting can provide a practical, visual, low-cost approach to indoor positioning.

The goal is to prove the core idea:

**Indoor spaces are searchable, navigable, and measurable using the signals already in the air.**