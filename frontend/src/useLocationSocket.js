import { useEffect, useRef, useState } from 'react'

// The backend broadcasts {"x": ..., "y": ...} over this websocket every time
// the scanner sends a reading. We default to the same host the page is served
// from (so opening the site from a phone/another laptop on the same Wi-Fi just
// works), on the backend's port 8000. Override with VITE_WS_URL if needed.
const WS_URL =
  import.meta.env.VITE_WS_URL ||
  `ws://${window.location.hostname || 'localhost'}:8000/ws`

const MAX_TRAIL = 25

/**
 * Connects to the backend location websocket and exposes the live position,
 * a short trail of recent points, and the connection status. Auto-reconnects
 * if the backend restarts.
 */
export function useLocationSocket() {
  const [status, setStatus] = useState('connecting')
  const [position, setPosition] = useState(null)
  const [trail, setTrail] = useState([])
  const socketRef = useRef(null)
  const reconnectRef = useRef(null)

  useEffect(() => {
    let closed = false

    function connect() {
      setStatus('connecting')
      const socket = new WebSocket(WS_URL)
      socketRef.current = socket

      socket.onopen = () => setStatus('connected')

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (typeof data.x !== 'number' || typeof data.y !== 'number') return

          const point = { x: data.x, y: data.y }
          setPosition(point)
          setTrail((prev) => [...prev, point].slice(-MAX_TRAIL))
        } catch {
          // Ignore malformed messages.
        }
      }

      socket.onclose = () => {
        setStatus('disconnected')
        if (!closed) {
          reconnectRef.current = setTimeout(connect, 1500)
        }
      }

      socket.onerror = () => socket.close()
    }

    connect()

    return () => {
      closed = true
      clearTimeout(reconnectRef.current)
      socketRef.current?.close()
    }
  }, [])

  return { status, position, trail }
}
