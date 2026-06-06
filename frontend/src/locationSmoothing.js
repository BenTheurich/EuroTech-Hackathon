export const MAX_TRAIL = 60
export const TRAIL_INTERVAL_MS = 180
export const TRAIL_MIN_DISTANCE = 0.05

const SMOOTHING_SPEED = 8

export function advanceDisplayedPosition(current, target, deltaSeconds) {
  if (!target) return current
  if (!current) return { ...target }

  const alpha = 1 - Math.exp(-SMOOTHING_SPEED * Math.max(deltaSeconds, 0))
  const x = current.x + (target.x - current.x) * alpha
  const y = current.y + (target.y - current.y) * alpha

  return {
    ...target,
    x,
    y,
  }
}

export function confidenceRingRadius(confidence) {
  const clamped = clamp(confidence ?? 1, 0.15, 1)
  const radius = 0.24 + (1 - clamped) * 0.4470588235
  return Number(radius.toFixed(2))
}

export function shouldAppendTrailPoint(lastPoint, nextPoint, elapsedMs) {
  if (!nextPoint) return false
  if (!lastPoint) return true
  if (elapsedMs < TRAIL_INTERVAL_MS) return false

  return distance(lastPoint, nextPoint) >= TRAIL_MIN_DISTANCE
}

function distance(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y)
}

function clamp(value, minimum, maximum) {
  return Math.max(minimum, Math.min(maximum, value))
}
