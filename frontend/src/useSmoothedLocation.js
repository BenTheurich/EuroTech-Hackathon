import { useEffect, useRef, useState } from 'react'
import {
  MAX_TRAIL,
  advanceDisplayedPosition,
  shouldAppendTrailPoint,
} from './locationSmoothing'

export function useSmoothedLocation(targetPosition) {
  const [position, setPosition] = useState(null)
  const [trail, setTrail] = useState([])
  const targetRef = useRef(null)
  const currentRef = useRef(null)
  const lastFrameRef = useRef(null)
  const lastTrailPointRef = useRef(null)
  const lastTrailAtRef = useRef(0)

  useEffect(() => {
    targetRef.current = targetPosition

    if (targetPosition && !currentRef.current) {
      currentRef.current = { ...targetPosition }
      lastTrailPointRef.current = { ...targetPosition }
      setPosition({ ...targetPosition })
      setTrail([{ ...targetPosition }])
    }
  }, [targetPosition])

  useEffect(() => {
    let frameId

    function frame(now) {
      const previousFrame = lastFrameRef.current ?? now
      const deltaSeconds = Math.min((now - previousFrame) / 1000, 0.25)
      lastFrameRef.current = now

      const next = advanceDisplayedPosition(
        currentRef.current,
        targetRef.current,
        deltaSeconds,
      )

      if (next) {
        currentRef.current = next
        setPosition(next)

        const trailElapsed = now - lastTrailAtRef.current
        if (shouldAppendTrailPoint(lastTrailPointRef.current, next, trailElapsed)) {
          lastTrailPointRef.current = { x: next.x, y: next.y }
          lastTrailAtRef.current = now
          setTrail((prev) => [...prev, { x: next.x, y: next.y }].slice(-MAX_TRAIL))
        }
      }

      frameId = requestAnimationFrame(frame)
    }

    frameId = requestAnimationFrame(frame)
    return () => cancelAnimationFrame(frameId)
  }, [])

  return { position, trail }
}
