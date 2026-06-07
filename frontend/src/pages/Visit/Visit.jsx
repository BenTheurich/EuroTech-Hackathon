import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useLocationSocket } from '../../useLocationSocket';
import { useSmoothedLocation } from '../../useSmoothedLocation';
import { findRoute } from '../../components/GridFloorPlan/gridRouting';
import VisitorMap from '../../components/VisitorMap/VisitorMap';
import {
  VENUE,
  DESTINATIONS,
  CATEGORIES,
  ROUTE_PREFERENCES,
  FLOOR_FEATURES,
  generateVenueWalls,
} from './destinations';
import Icon from '../../components/Icon/Icon';
import styles from './Visit.module.css';

const STATUS_LABELS = {
  connecting: 'Locating you…',
  connected: 'Live tracking',
  disconnected: 'Reconnecting…',
};

export default function Visit() {
  const [step, setStep] = useState('welcome'); // welcome → prefs → navigate
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('all');
  const [destinationId, setDestinationId] = useState(null);
  const [preferenceId, setPreferenceId] = useState('fastest');

  // Live position from the backend KNN websocket (same source as /live).
  const { status, targetPosition } = useLocationSocket();
  const { position } = useSmoothedLocation(targetPosition);

  // A fresh, complex, fully-connected floor for this session (stable across the
  // welcome → prefs → navigate steps; reload the page for a new layout).
  const walls = useMemo(() => generateVenueWalls(), []);
  const destination = DESTINATIONS.find((d) => d.id === destinationId) || null;

  // Best-path Dijkstra route from the live position to the chosen POI, computed
  // client-side over the walls we draw. Recomputing in this memo means the route
  // auto-updates the instant the user moves (re-plans as they follow it or stray
  // off it) or the floor's walls change (e.g. a wall is removed).
  const route = useMemo(() => {
    if (!position || !destination) return null;
    return findRoute(
      { x: position.x, y: position.y },
      { x: destination.x, y: destination.y },
      walls,
      preferenceId,
    );
  }, [position, destination, walls, preferenceId]);

  const distanceMeters =
    route?.reachable && typeof route.distance === 'number'
      ? Math.round(route.distance)
      : position && destination
        ? Math.round(Math.hypot(destination.x - position.x, destination.y - position.y))
        : null;

  const chooseDestination = (id) => {
    setDestinationId(id);
    setStep('prefs');
  };

  return (
    <div className={styles.shell}>
      <header className={styles.topbar}>
        <div className={styles.brand}>
          <span className={styles.brandIcon}>◈</span>
          <div>
            <div className={styles.brandName}>RmFindr</div>
            <div className={styles.brandSub}>{VENUE.name} · {VENUE.floorLabel}</div>
          </div>
        </div>
        <Link to="/" className={styles.adminLink}>Admin ↗</Link>
      </header>

      <main className={styles.main}>
        {step === 'welcome' && (
          <WelcomeStep
            query={query}
            setQuery={setQuery}
            category={category}
            setCategory={setCategory}
            onChoose={chooseDestination}
          />
        )}

        {step === 'prefs' && destination && (
          <PrefsStep
            destination={destination}
            preferenceId={preferenceId}
            setPreferenceId={setPreferenceId}
            onBack={() => setStep('welcome')}
            onStart={() => setStep('navigate')}
          />
        )}

        {step === 'navigate' && destination && (
          <NavigateStep
            walls={walls}
            position={position}
            destination={destination}
            route={route}
            preferenceId={preferenceId}
            distanceMeters={distanceMeters}
            statusLabel={STATUS_LABELS[status] || status}
            statusKey={status}
            onChange={() => setStep('welcome')}
          />
        )}
      </main>
    </div>
  );
}

function WelcomeStep({ query, setQuery, category, setCategory, onChoose }) {
  const q = query.trim().toLowerCase();
  const list = DESTINATIONS.filter(
    (d) =>
      (category === 'all' || d.category === category) &&
      (q === '' || d.label.toLowerCase().includes(q)),
  );

  return (
    <div className={styles.welcome}>
      <span className={styles.kicker}>Welcome</span>
      <h1 className={styles.question}>Where do you want to go?</h1>
      <p className={styles.lede}>
        Pick your destination and we’ll guide you there from where you’re standing.
      </p>

      <input
        className={styles.search}
        type="search"
        placeholder="Search rooms, facilities, exits…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      <div className={styles.chips}>
        {CATEGORIES.map((c) => (
          <button
            key={c.id}
            className={`${styles.chip} ${category === c.id ? styles.chipActive : ''}`}
            onClick={() => setCategory(c.id)}
          >
            {c.label}
          </button>
        ))}
      </div>

      <div className={styles.destGrid}>
        {list.map((d) => (
          <button key={d.id} className={styles.destCard} onClick={() => onChoose(d.id)}>
            <span className={styles.destCardIcon}><Icon icon={d.icon} alt="" /></span>
            <span className={styles.destCardLabel}>{d.label}</span>
            <span className={styles.destCardGo}>→</span>
          </button>
        ))}
        {list.length === 0 && (
          <p className={styles.empty}>No destinations match your search.</p>
        )}
      </div>
    </div>
  );
}

function PrefsStep({ destination, preferenceId, setPreferenceId, onBack, onStart }) {
  return (
    <div className={styles.prefs}>
      <button className={styles.backBtn} onClick={onBack}>← Change destination</button>

      <div className={styles.prefsHead}>
        <span className={styles.prefsDestIcon}><Icon icon={destination.icon} alt="" /></span>
        <div>
          <span className={styles.prefsDestLabel}>Going to {destination.label}</span>
          <span className={styles.prefsDestSub}>{VENUE.name}</span>
        </div>
      </div>

      <h2 className={styles.question}>How would you like to get there?</h2>

      <div className={styles.prefList}>
        {ROUTE_PREFERENCES.map((p) => (
          <button
            key={p.id}
            className={`${styles.prefCard} ${preferenceId === p.id ? styles.prefCardActive : ''}`}
            onClick={() => setPreferenceId(p.id)}
          >
            <span className={styles.prefIcon}><Icon icon={p.icon} alt="" /></span>
            <span className={styles.prefText}>
              <span className={styles.prefLabel}>{p.label}</span>
              <span className={styles.prefHint}>{p.hint}</span>
            </span>
            <span className={styles.prefRadio} aria-hidden="true" />
          </button>
        ))}
      </div>

      <button className={styles.startBtn} onClick={onStart}>Start navigation</button>
    </div>
  );
}

function NavigateStep({
  walls,
  position,
  destination,
  route,
  preferenceId,
  distanceMeters,
  statusLabel,
  statusKey,
  onChange,
}) {
  const pref = ROUTE_PREFERENCES.find((p) => p.id === preferenceId);

  return (
    <div className={styles.navigate}>
      <div className={styles.navBar}>
        <button className={styles.backBtn} onClick={onChange}>← Change destination</button>
        <span className={`${styles.statusPill} ${styles[`status_${statusKey}`] || ''}`}>
          <span className={styles.statusDot} />
          {statusLabel}
        </span>
      </div>

      <div className={styles.navLayout}>
        <div className={styles.mapCard}>
          <VisitorMap
            walls={walls}
            position={position}
            destination={destination}
            route={route}
            features={FLOOR_FEATURES}
          />
        </div>

        <aside className={styles.panel}>
          <div className={styles.panelCard}>
            <span className={styles.panelKicker}>Destination</span>
            <div className={styles.panelDest}>
              <span className={styles.panelDestIcon}><Icon icon={destination.icon} alt="" /></span>
              <span className={styles.panelDestLabel}>{destination.label}</span>
            </div>
            <div className={styles.panelRow}>
              <span className={styles.panelLabel}>Distance</span>
              <span className={styles.panelValue}>
                {distanceMeters != null ? `≈ ${distanceMeters} m` : 'Locating…'}
              </span>
            </div>
            <div className={styles.panelRow}>
              <span className={styles.panelLabel}>Route</span>
              <span className={styles.panelValue}><Icon icon={pref?.icon} alt="" /> {pref?.label}</span>
            </div>
            <div className={styles.panelRow}>
              <span className={styles.panelLabel}>Your position</span>
              <span className={styles.panelValue}>
                {position ? `x ${position.x.toFixed(1)} · y ${position.y.toFixed(1)}` : '—'}
              </span>
            </div>
          </div>

          <div className={styles.panelCard}>
            <span className={styles.panelKicker}>Guidance</span>
            <p className={styles.guidance}>
              {position
                ? `Follow the blue line toward ${destination.label}. The dot is your live position.`
                : 'Waiting for your live position from the venue sensors…'}
            </p>
          </div>

          <div className={styles.legend}>
            <span className={styles.legendItem}><span className={styles.lgUser} /> You</span>
            <span className={styles.legendItem}><span className={styles.lgDest} /> Destination</span>
            <span className={styles.legendItem}><span className={styles.lgAnchor} /> Wi-Fi anchor</span>
            <span className={styles.legendItem}><span aria-hidden="true">🛗</span> Stairs &amp; lift</span>
          </div>
        </aside>
      </div>
    </div>
  );
}
