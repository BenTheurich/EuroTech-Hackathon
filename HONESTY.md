# HONESTY.md

---

## 1. Team - who did what

Judges compare this against `git shortlog -sn`, so keep it honest.

| Member | GitHub handle | Main contributions |
|---|---|---|
| Ben Theurich | @BenTheurich | Project scoping and README, FastAPI/WebSocket backend, KNN localizer, tracking filters, anchor hints, scanner/replay tooling, fingerprint cleaning, tests, integration docs, and deliverables. |
| Daria Pop | @Daria2oo6 | Frontend UI and visitor-interface iterations, visual/theme work, icons/assets, and layout/design updates. |
| ClbVictor | @ClbVictor | Scanner testing and tuning, fingerprint data work, stale-scan/anchor threshold improvements, model edge-case fixes, and README updates. |
| SoDa | @SoDa / git author `SoDa` | Frontend design work and Dijkstra/pathfinding prototype work in the git history; not part of the current live KNN positioning loop. |

---

## 2. What is fully working

- **Real Windows Wi-Fi scanner:** `scanner/scanner.py` uses `pywifi` to trigger real Wi-Fi scans, match the configured anchor SSIDs, convert signal values to approximate dBm, briefly carry forward missing anchors, write `data/latest_scan.json`, and POST scan payloads to the backend. Input: nearby Wi-Fi scan results from the laptop. Output: JSON with `rssi_a`, `rssi_b`, `rssi_c`, `rssi_d`, timing metadata, scan count, and carry-forward metadata.
- **Backend indoor location estimate:** `backend/main.py` exposes `POST /api/location-data`, median-filters the RSSI payload, runs a scikit-learn distance-weighted KNN regressor through `backend/knn_model.py`, applies anchor hints and movement constraints, and broadcasts a location payload over WebSocket. Input: four RSSI values plus optional metadata. Output: `x`, `y`, raw KNN position, confidence, status, nearest-distance diagnostics, carried anchors, and timestamp.
- **React live map:** the frontend connects to `ws://<host>:8000/ws`, receives the backend payload, smooths the target position, and renders a 7 m x 5 m room map with four fixed anchors, a live position dot, confidence ring, recent movement trail, and position/confidence footer. Input: WebSocket location messages. Output: live indoor-map visualization in the browser.
- **Local fingerprint dataset and cleaning flow:** the repo includes collected fingerprint CSVs, including `data/fingerprints1400_clean.csv` with 1,400 rows. `backend/fingerprint_cleaner.py` can fill missing RSSI values and records imputation flags, while `backend/prepare_fingerprints.py` regenerates the cleaned CSV from raw measurements.
- **Development replay utilities:** `scanner/replay_recorded_walk.py` can replay recorded scanner logs/CSVs through the real backend, and `scanner/profile_scan_rate.py` profiles scan waits on the demo laptop. These are useful for testing and tuning, but replay is not the same as a live hardware scan.

---

## 3. What is mocked, stubbed, or hardcoded

The live positioning path is not mocked when we run `scanner/scanner.py`: the laptop reads real Wi-Fi scans, the backend runs the KNN/tracker logic, and the frontend renders real WebSocket updates from the backend.

The items below are either development/testing utilities we used so we did not have to physically walk the laptop around for every frontend/model change, or hackathon-scope assumptions for the room setup. Nothing in the live scanner path returns a pre-scripted location.

| What is mocked, test-only, or hardcoded | Where (file:line or folder) | How it is used | What the production version would do |
|---|---|---|---|
| Simulated Wi-Fi walker / generated RSSI path. | `scanner/simulate_walk.py:2`, `scanner/simulate_walk.py:5`, `scanner/simulate_walk.py:32`, `scanner/simulate_walk.py:40` | Development-only helper for frontend and algorithm testing. It lets us see the map move without carrying the laptop around the room after every code change. It is not the live scanner. | Use `scanner/scanner.py` with real phone hotspot anchors and live laptop Wi-Fi scans. |
| Recorded-walk replay. | `scanner/replay_recorded_walk.py:151`, `scanner/replay_recorded_walk.py:218`, `scanner/replay_recorded_walk.py:228`, `scanner/replay_recorded_walk.py:328` | Development/debug helper that replays previously captured scanner output through the same backend. Useful for repeatable testing of smoothing, confidence, and frontend behavior. | Read current Wi-Fi scans from the moving device in real time. |
| Demo-room geometry, anchor positions, and anchor SSID names are configured in code. | `frontend/src/MapView.jsx:12`, `frontend/src/MapView.jsx:14`, `scanner/scanner.py:15`, `backend/anchor_hints.py:6` | Hackathon-scope setup for one known 7 m x 5 m room with four known anchors. The values match the collected fingerprint dataset. | Load venue, floor, anchor, and SSID configuration from a setup flow or database and support multiple rooms/floors. |
| Backend trains from a static local fingerprint CSV by default. | `backend/main.py:34`, `backend/knn_model.py:119`, `backend/knn_model.py:126`, `data/fingerprints1400_clean.csv` | The CSV is real collected calibration data, not fake responses. The shortcut is that calibration is file-based and preloaded rather than managed live through the app UI. | Persist calibration points through an API/database, retrain or update the model per venue, and version fingerprint maps. |
| A small number of missing RSSI values in cleaned CSVs are imputed. | `backend/fingerprint_cleaner.py:57`, `backend/fingerprint_cleaner.py:64`, `data/fingerprints1400_clean.csv` | Data-cleaning shortcut: `data/fingerprints1400_clean.csv` has 28 imputed RSSI cells out of 5,600 RSSI cells, and the imputed cells are marked in the CSV. | Collect more repeated scans per point or use a model/input pipeline that can handle missing anchor values directly. |
| Optional blended-fingerprint generator uses synthetic/interpolated RSSI priors. | `backend/blended_fingerprints.py:14`, `backend/blended_fingerprints.py:23`, `backend/blended_fingerprints.py:51`, `backend/blended_fingerprints.py:69` | Experimental calibration helper. It is not the default live training file unless `WIFI_FINGERPRINT_PATH` is explicitly pointed at its output. | Use measured fingerprints from a proper site survey or a validated learned propagation model. |
| Tiny fallback/toy fingerprint dataset. | `backend/knn_model.py:119`, `backend/knn_model.py:126`, `data/sample_fingerprints.csv` | Test/local fallback only, so code paths can run when a real dataset is absent. The default live demo uses `data/fingerprints1400_clean.csv`. | Require a real venue fingerprint dataset before starting live positioning. |
| Simple SVG room grid instead of a real imported floor plan. | `frontend/src/MapView.jsx:36`, `frontend/src/MapView.jsx:91` | Visual simplification for the room-scale technical demo. The position dot, trail, anchors, and confidence display are real frontend logic. | Render a real floor-plan image/vector map aligned to the same coordinate system as the fingerprints. |
| CORS is open to all origins. | `backend/main.py:18` | Local demo convenience so laptops and phones on the same network can connect quickly. | Restrict allowed origins, add authentication/authorization, and separate demo config from production config. |

---

## 4. External APIs, services & data sources

Everything the project calls or pretends to call. Mark each as real or mocked.

| Service / API / dataset | Used for | Real call or mocked? | Auth (sandbox / test key / none) |
|---|---|---|---|
| Windows Wi-Fi scanning through `pywifi` / Native Wi-Fi APIs | Reads nearby Wi-Fi networks and RSSI values from the laptop scanner. | Real local OS call. | None. |
| Local FastAPI backend `POST /api/location-data` | Receives scanner RSSI payloads and runs localization. | Real local HTTP call. | None. |
| Local WebSocket endpoint `/ws` | Streams backend location updates to the React dashboard. | Real local WebSocket call. | None. |
| `data/fingerprints1400_clean.csv` and other CSV fingerprint files | Training data for the KNN localizer and calibration experiments. | Real collected local data, with disclosed cleaning/imputation. | None. |
| `data/sample_fingerprints.csv` | Fallback/test fingerprint dataset. | Mocked/toy data. | None. |
| scikit-learn `KNeighborsRegressor` | Converts RSSI vectors into estimated `(x, y)` positions. | Real library call. | None. |
| Phone hotspot anchors / configured SSIDs | Physical Wi-Fi signal references for the demo. | Real hardware signals when using `scanner/scanner.py`; mocked only by simulator/replay utilities. | None in repo. |
| `scanner/simulate_walk.py` | Hardware-free demo/dev signal source. | Mocked. | None. |
| `scanner/replay_recorded_walk.py` | Replays saved scanner output through the real backend. | Mocked input, real backend call. | None. |
| React/Vite frontend | Browser UI for the live map. | Real local app. | None. |

No cloud AI, payment, map/geocoding, database, Supabase, Firebase, or third-party hosted API is used by the current app.

---

## 5. Pre-existing code

Anything written **before** kickoff that we brought into this project: prior personal projects, forked open-source code, templates, boilerplate, internal libraries.

| Item | Source (URL or description) | Roughly how much | License |
|---|---|---|---|
| Vite/React starter scaffold and default assets | Standard Vite React project scaffold visible in `frontend/package.json`, `frontend/index.html`, and default `vite.svg` / `react.svg` assets. | Frontend project shell/config plus default starter assets; app-specific map/socket/tracking UI code is custom. | Vite/React ecosystem is open source, primarily MIT; verify individual package licenses before production. |
| Open-source npm and PyPI dependencies | Packages declared in `frontend/package.json`, `backend/requirements.txt`, and `scanner/requirements.txt`. | Imported libraries only; they are not vendored into the repo. | Package-specific open-source licenses. |
| Prior personal project or forked application code | None | 0 app-specific files. | N/A. |

---

## 6. Known limitations & next steps


- The current live scanner localizes a laptop, not a consumer phone. The docs note that iOS blocks Wi-Fi signal reads and Android throttles them; phones can view the map but are not the scanner.
- The production asset-tracking version would need ESP32-class tags or other controlled hardware, not ordinary visitor phones.
- The current implementation expects four anchor signals, and the code and current default dataset use four anchors.
- The app is calibrated for one 7 m x 5 m demo room. It does not yet support multiple rooms, multiple floors, floor transitions, venue setup, or uploaded floor plans.
- The frontend does not yet provide a full calibration UI for clicking/saving points. Calibration is handled through scanner/CSV scripts and static datasets.
- Accuracy is zone-level, not sub-meter or shelf-level. The README states this explicitly; production would require denser calibration, better confidence modeling, and measured validation.
- The backend has no auth, no user/session model, no database, open CORS, and no production deployment hardening.
- RSSI scans are noisy and OS-dependent. Windows scan timing has to be profiled on the actual demo laptop, and stale/missing anchors can still reduce accuracy.
- Next steps: venue/floor configuration, real floor-plan alignment, calibration-management UI/API, persisted fingerprint database, multi-floor model, controlled hardware tags, better missing-anchor handling, measured accuracy reports, and privacy-preserving aggregate analytics.
