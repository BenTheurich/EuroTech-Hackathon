import assert from 'node:assert/strict'

import {
  advanceDisplayedPosition,
  confidenceRingRadius,
  shouldAppendTrailPoint,
} from './locationSmoothing.js'

const next = advanceDisplayedPosition(
  { x: 0, y: 0 },
  { x: 4, y: 0 },
  0.1,
)

assert(next.x > 0)
assert(next.x < 4)
assert.equal(next.y, 0)

assert.equal(
  advanceDisplayedPosition(null, { x: 2, y: 3 }, 0.1).x,
  2,
)

assert.equal(confidenceRingRadius(1), 0.24)
assert.equal(confidenceRingRadius(0.15), 0.62)

assert.equal(
  shouldAppendTrailPoint({ x: 0, y: 0 }, { x: 0.04, y: 0 }, 200),
  false,
)
assert.equal(
  shouldAppendTrailPoint({ x: 0, y: 0 }, { x: 0.06, y: 0 }, 179),
  false,
)
assert.equal(
  shouldAppendTrailPoint({ x: 0, y: 0 }, { x: 0.06, y: 0 }, 180),
  true,
)
