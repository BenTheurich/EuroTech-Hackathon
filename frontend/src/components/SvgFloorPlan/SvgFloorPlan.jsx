import styles from './SvgFloorPlan.module.css';

// Simple placeholder SVG floor plan
// Replace this with dynamically loaded SVG files when upload is implemented
export default function SvgFloorPlan({ children }) {
  return (
    <div className={styles.container}>
      <svg
        viewBox="0 0 480 380"
        className={styles.svg}
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* ── Outer walls ── */}
        <rect x="20" y="20" width="440" height="340" fill="#f8f9fb" stroke="#2c3e50" strokeWidth="3" rx="2" />

        {/* ── Corridors (horizontal + vertical) ── */}
        <rect x="20" y="170" width="440" height="50" fill="#e9ecef" stroke="none" />
        <rect x="200" y="20" width="50" height="340" fill="#e9ecef" stroke="none" />

        {/* ── Rooms top-left quadrant ── */}
        <rect x="20" y="20" width="180" height="150" fill="#fff" stroke="#95a5a6" strokeWidth="1.5" />
        <text x="85" y="95" textAnchor="middle" className={styles.roomLabel}>Room 101</text>
        <text x="85" y="110" textAnchor="middle" className={styles.roomSubLabel}>Lecture Hall</text>

        {/* Door top-left room */}
        <rect x="115" y="168" width="30" height="4" fill="#e9ecef" stroke="none" />
        <path d="M115 170 Q130 155 145 170" fill="none" stroke="#7f8c8d" strokeWidth="1" strokeDasharray="2,2" />

        {/* ── Rooms top-right quadrant ── */}
        <rect x="250" y="20" width="100" height="150" fill="#fff" stroke="#95a5a6" strokeWidth="1.5" />
        <text x="300" y="95" textAnchor="middle" className={styles.roomLabel}>Room 102</text>
        <text x="300" y="110" textAnchor="middle" className={styles.roomSubLabel}>Lab A</text>

        <rect x="350" y="20" width="110" height="150" fill="#fff" stroke="#95a5a6" strokeWidth="1.5" />
        <text x="405" y="95" textAnchor="middle" className={styles.roomLabel}>Room 103</text>
        <text x="405" y="110" textAnchor="middle" className={styles.roomSubLabel}>Lab B</text>

        {/* Doors top-right */}
        <rect x="248" y="115" width="4" height="28" fill="#e9ecef" stroke="none" />
        <path d="M250 115 Q265 130 250 143" fill="none" stroke="#7f8c8d" strokeWidth="1" strokeDasharray="2,2" />

        {/* ── Rooms bottom-left quadrant ── */}
        <rect x="20" y="220" width="120" height="140" fill="#fff" stroke="#95a5a6" strokeWidth="1.5" />
        <text x="80" y="285" textAnchor="middle" className={styles.roomLabel}>Room 104</text>
        <text x="80" y="300" textAnchor="middle" className={styles.roomSubLabel}>Office</text>

        <rect x="140" y="220" width="60" height="140" fill="#fff" stroke="#95a5a6" strokeWidth="1.5" />
        <text x="170" y="285" textAnchor="middle" className={styles.roomLabel}>105</text>
        <text x="170" y="300" textAnchor="middle" className={styles.roomSubLabel}>WC</text>

        {/* Door bottom-left */}
        <rect x="115" y="218" width="28" height="4" fill="#e9ecef" stroke="none" />
        <path d="M115 220 Q130 205 143 220" fill="none" stroke="#7f8c8d" strokeWidth="1" strokeDasharray="2,2" />

        {/* ── Rooms bottom-right quadrant ── */}
        <rect x="250" y="220" width="210" height="140" fill="#fff" stroke="#95a5a6" strokeWidth="1.5" />
        <text x="355" y="285" textAnchor="middle" className={styles.roomLabel}>Room 106</text>
        <text x="355" y="300" textAnchor="middle" className={styles.roomSubLabel}>Seminar Room</text>

        {/* Door bottom-right */}
        <rect x="248" y="255" width="4" height="28" fill="#e9ecef" stroke="none" />
        <path d="M250 255 Q265 270 250 283" fill="none" stroke="#7f8c8d" strokeWidth="1" strokeDasharray="2,2" />

        {/* ── Staircase / Elevator ── */}
        <rect x="20" y="170" width="60" height="50" fill="#dfe6e9" stroke="#b2bec3" strokeWidth="1.5" />
        <line x1="20" y1="182" x2="80" y2="182" stroke="#b2bec3" strokeWidth="1" />
        <line x1="20" y1="194" x2="80" y2="194" stroke="#b2bec3" strokeWidth="1" />
        <line x1="20" y1="206" x2="80" y2="206" stroke="#b2bec3" strokeWidth="1" />
        <text x="50" y="223" textAnchor="middle" className={styles.roomSubLabel}>Stairs</text>

        {/* Elevator */}
        <rect x="420" y="170" width="40" height="50" fill="#dfe6e9" stroke="#b2bec3" strokeWidth="1.5" rx="3" />
        <text x="440" y="191" textAnchor="middle" className={styles.roomSubLabel}>Lift</text>
        <text x="440" y="205" textAnchor="middle" fontSize="14">⬆</text>

        {/* ── Corridor labels ── */}
        <text x="135" y="200" textAnchor="middle" className={styles.corridorLabel}>Main Corridor</text>
        <text x="225" y="110" textAnchor="middle" className={styles.corridorLabel} transform="rotate(-90, 225, 110)">Hallway</text>

        {/* ── Wi-Fi Access Points ── */}
        <WifiMarker cx="110" cy="80" label="AP-1" />
        <WifiMarker cx="320" cy="80" label="AP-2" />
        <WifiMarker cx="225" cy="195" label="AP-3" />
        <WifiMarker cx="355" cy="290" label="AP-4" />

        {/* Overlay slot for position markers */}
        {children}
      </svg>
    </div>
  );
}

function WifiMarker({ cx, cy, label }) {
  return (
    <g>
      <circle cx={cx} cy={cy} r="10" fill="#3498db" fillOpacity="0.15" stroke="#3498db" strokeWidth="1.5" />
      <circle cx={cx} cy={cy} r="3" fill="#3498db" />
      <path
        d={`M${cx - 7} ${cy - 4} Q${cx} ${cy - 12} ${cx + 7} ${cy - 4}`}
        fill="none" stroke="#3498db" strokeWidth="1.5" strokeLinecap="round"
      />
      <path
        d={`M${cx - 4} ${cy - 1} Q${cx} ${cy - 7} ${cx + 4} ${cy - 1}`}
        fill="none" stroke="#3498db" strokeWidth="1.5" strokeLinecap="round"
      />
      <text x={cx} y={cy + 20} textAnchor="middle" fontSize="8" fill="#3498db" fontFamily="sans-serif">{label}</text>
    </g>
  );
}
