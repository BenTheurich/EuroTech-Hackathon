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
   { "rssi_a": -55, "rssi_b": -38, "rssi_c": -44, "rssi_d": -57 }
   ```

2. Backend -> Frontend: WebSocket `ws://<host>:8000/ws`
   ```json
   { "x": 3.2, "y": 1.7 }
   ```

3. Coordinate space: `x` and `y` live in the same space the KNN is trained on.
   The frontend `FLOOR` and `ANCHORS` constants match the collected fingerprint
   map: `x = 0..7`, `y = 0..5`.

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

Feed the map with no hardware:

```bash
pip install requests
python scanner/simulate_walk.py
```

Feed the map from the real Windows scanner:

```bash
py -m pip install -r scanner/requirements.txt
py scanner/scanner.py
```

Edit `BACKEND_URL` in `scanner.py` if the backend runs on a different laptop.

## Viewing from a phone

Phone and laptop must be on the same Wi-Fi. Start the frontend with:

```bash
npm run dev -- --host
```

Then open `http://<laptop-LAN-IP>:5173` on the phone. The map auto-connects to
the backend at the same hostname on port 8000.
