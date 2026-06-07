# How the pieces fit together

```text
[Windows laptop]                 [any laptop]                  [browser]
 scanner/scanner.py   --POST-->   backend/main.py   --WebSocket-->  frontend
 reads Wi-Fi RSSI                 KNN: RSSI -> (x,y)               draws the dot
```

The laptop is the device being located. Phones can only view the map. iOS,
Android, and browsers do not allow reading Wi-Fi signal strength, so a phone
cannot be the scanner. We localize laptops and demo the tech on them.

## The data contract

1. Scanner -> Backend: HTTP `POST /api/location-data`
   ```json
   {
     "rssi_a": -55,
     "rssi_b": -38,
     "rssi_c": -44,
     "rssi_d": -57,
     "scan_id": 12,
     "scan_started_at": "2026-06-06T16:10:04.120",
     "scan_finished_at": "2026-06-06T16:10:04.905",
     "scan_wait_seconds": 0.75,
     "network_count": 18,
     "carried": []
   }
   ```

   Only the four `rssi_*` fields are required. The scanner adds timing and
   carry-forward metadata so the backend can estimate confidence.

2. Backend -> Frontend: WebSocket `ws://<host>:8000/ws`
   ```json
   {
     "x": 3.2,
     "y": 1.7,
     "raw_x": 3.4,
     "raw_y": 1.8,
     "confidence": 0.86,
     "status": "live",
     "nearest_distance": 6.2,
     "scan_age_ms": 140,
     "carried": [],
     "timestamp": "2026-06-06T16:10:05.040+00:00"
   }
   ```

   `x` and `y` are the movement-constrained display target. `raw_x` and
   `raw_y` are the direct KNN prediction. `status` is `live`,
   `low_confidence`, `smoothed`, or `constrained`.

3. Coordinate space: `x` and `y` live in the same space the KNN is trained on.
   The frontend `FLOOR` and `ANCHORS` constants match the collected fingerprint
   map: `x = 0..7`, `y = 0..5`.

4. Navigation routing. Walls are impassable segments on the lattice edges (the
   same `h-x-y` / `v-x-y` keys the editor draws). The route runs **straight**
   where the floor is open and **bends only where a wall blocks the way**, and
   it never crosses a wall or squeezes diagonally between two walls that meet at
   a corner. Method:

   * Line of sight is tested with a **DDA grid march** — it walks the cells a
     straight line passes through and checks the actual cell edge it crosses
     each step. At a diagonal vertex it requires one of the two L-detours around
     the corner to be fully open, which is what prevents corner cutting.
   * The path is the shortest route over a **visibility graph of the cell
     centres** (+ the real start and goal); cell centres sit off every wall
     line, so routing is robust. Dijkstra picks the shortest clear path.

   Two equivalent implementations share these semantics:

   * `frontend/src/components/GridFloorPlan/gridRouting.js` runs **in the
     browser** and powers the visitor map. Routing client-side lets the path
     re-plan instantly as the user moves (follows it or strays off it) and the
     moment a wall is added/removed, with no per-move round-trip and no straight
     line through walls if the backend is briefly unreachable. The live position
     still comes from the backend `/ws`; only the path search is local.
   * `backend/pathfinding.py`, exposed as HTTP `POST /api/route`, is the
     equivalent **server-side** API for other clients.

   The visitor floor itself is generated fresh each session by
   `frontend/src/components/GridFloorPlan/floorGen.js` (a randomized,
   guaranteed-connected rooms-and-corridors layout), so every destination stays
   reachable while the router has real walls to work around. A destination that
   is walled off entirely returns `reachable: false` with a direct-segment
   fallback.

   ```json
   {
     "start": {"x": 3.2, "y": 1.7},
     "goal":  {"x": 6.4, "y": 4.4},
     "walls": ["h-0-0", "v-2-3"],
     "preference": "fastest"
   }
   ```

   Response:

   ```json
   {
     "status": "success",
     "reachable": true,
     "preference": "fastest",
     "path": [{"x": 3.2, "y": 1.7}, {"x": 5, "y": 3}, {"x": 6.4, "y": 4.4}],
     "distance": 4.86
   }
   ```

   `path` starts at the real position and ends at the real destination, with a
   wall corner in between only where the route has to turn.

   `walls` is optional; the backend falls back to the venue floor in
   `pathfinding.default_walls` when it is absent. See `backend/pathfinding.py`.

Training uses `data/fingerprints_clean.csv` when it exists. That file is
generated from `data/fingerprints.csv` and keeps the raw measurements untouched.

## Running it

Backend:

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Prepare fingerprint data after collecting or changing `data/fingerprints.csv`:

```bash
python backend/prepare_fingerprints.py
```

Generate the route-calibrated blended dataset:

```bash
python backend/blended_fingerprints.py
```

Run the backend with that blended dataset:

```bash
$env:WIFI_FINGERPRINT_PATH="data/fingerprints_blended.csv"
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Feed the map with no hardware:

```bash
pip install requests
python scanner/simulate_walk.py
```

Feed the map from the real Windows scanner:

```bash
py -m pip install -r scanner/requirements.txt
py scanner/scanner.py --scan-wait 0.75 --interval 0 --quiet
```

If the backend runs on a different laptop, pass its LAN URL:

```bash
py scanner/scanner.py --backend-url http://192.168.1.50:8000/api/location-data
```

Measure the fastest reliable scan wait for the current Windows adapter:

```bash
py scanner/profile_scan_rate.py
```

The profiler sweeps scan waits from 0.25s to 4.0s and recommends the smallest
wait that sees all anchors in at least 90% of runs while keeping p90 loop time
close to the requested wait.

## Windows Wi-Fi scan limit

Windows does not expose a supported project-level switch to remove Wi-Fi scan
throttling for this scanner path. The Native Wi-Fi API's `WlanScan` call
returns immediately, and Microsoft documents that logo-compliant drivers should
complete scan requests within 4 seconds. Windows' own background scans can be
around 60 seconds or skipped while connected, so RmFindr triggers scans from the
app and tunes the wait empirically per adapter.

Use `scanner/profile_scan_rate.py` on the actual demo laptop and run the scanner
at the recommended `--scan-wait`. Going below that edge usually returns stale or
incomplete results, which makes the map less accurate even if the loop appears
faster.

## Viewing from a phone

Phone and laptop must be on the same Wi-Fi. Start the frontend with:

```bash
npm run dev -- --host
```

Then open `http://<laptop-LAN-IP>:5173` on the phone. The map auto-connects to
the backend at the same hostname on port 8000.
