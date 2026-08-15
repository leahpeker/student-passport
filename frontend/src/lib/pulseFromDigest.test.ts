/**
 * Plain assert checks over `pulseFromDigest`. No test framework.
 *
 *   npx tsx src/lib/pulseFromDigest.test.ts
 *
 * `pulseFromDigest` is the real-data path: it turns the backend's deterministic
 * one-day triage (`GET /students/<id>/digest/`) into the same `Pulse` shape the
 * UI already knows how to render. These guard that the mapping never invents a
 * tone the backend didn't compute, and never drops the backend's flags.
 */

import assert from 'node:assert/strict';
import { pulseFromDigest } from './pulse';
import type { Digest } from '../api/types';

let checks = 0;
function check(label: string, run: () => void): void {
  run();
  checks += 1;
  console.log(`  ✓ ${label}`);
}

function digest(overrides: Partial<Digest> = {}): Digest {
  return {
    student_id: 1,
    date: '2026-03-05',
    generated_at: '2026-03-05T12:00:00Z',
    record_count: 3,
    action: 'celebrate',
    headline: 'Solid day on fractions.',
    narrative: 'Worked through fractions cleanly, no signs of struggle.',
    topics: [
      { topic: 'fractions - adding', attempted: 8, correct: 7, accuracy: 0.875, avg_seconds: 22 },
    ],
    flags: [],
    insights: [],
    ...overrides,
  };
}

check('action "intervene" reads red, matching the backend triage', () => {
  const pulse = pulseFromDigest(digest({ action: 'intervene' }), 'Maya');
  assert.equal(pulse.tone, 'red');
});

check('action "check_in" reads amber', () => {
  const pulse = pulseFromDigest(digest({ action: 'check_in' }), 'Maya');
  assert.equal(pulse.tone, 'amber');
});

check('action "celebrate" reads green', () => {
  const pulse = pulseFromDigest(digest({ action: 'celebrate' }), 'Maya');
  assert.equal(pulse.tone, 'green');
});

check('the narrative becomes the "why", not a re-authored blurb', () => {
  const pulse = pulseFromDigest(
    digest({ narrative: 'Stuck on adding fractions today, faded across the session.' }),
    'Maya',
  );
  assert.equal(pulse.why, 'Stuck on adding fractions today, faded across the session.');
});

check('every backend flag becomes a signal — none are dropped', () => {
  const pulse = pulseFromDigest(
    digest({
      action: 'intervene',
      flags: [
        { topic: 'fractions - adding', kind: 'accuracy', severity: 'concern', detail: '2 of 8 correct today.' },
        { topic: 'fractions - adding', kind: 'pace', severity: 'watch', detail: 'Taking 1.9x as long as usual.' },
      ],
    }),
    'Maya',
  );
  assert.equal(pulse.signals.length, 2);
  assert.equal(pulse.signals[0].label, 'fractions - adding (accuracy)');
  assert.equal(pulse.signals[0].detail, '2 of 8 correct today.');
  assert.ok(pulse.signals[0].concerning, 'a concern-severity flag must read as concerning');
});

check('no flags means no signals — never invented', () => {
  const pulse = pulseFromDigest(digest({ flags: [] }), 'Maya');
  assert.equal(pulse.signals.length, 0);
});

check('topic accuracy becomes context, one entry per topic', () => {
  const pulse = pulseFromDigest(
    digest({
      topics: [
        { topic: 'fractions - adding', attempted: 8, correct: 2, accuracy: 0.25, avg_seconds: 30 },
      ],
    }),
    'Maya',
  );
  assert.equal(pulse.context.length, 1);
  assert.equal(pulse.context[0].label, 'fractions - adding');
  assert.equal(pulse.context[0].value, '2/8');
  assert.equal(pulse.context[0].tone, 'bad');
});

check('no app activity on file still produces a well-formed, honest pulse', () => {
  const pulse = pulseFromDigest(
    digest({
      date: null,
      action: 'check_in',
      headline: 'No app activity is on file for Maya yet.',
      narrative: '',
      topics: [],
      flags: [],
      insights: [],
    }),
    'Maya',
  );
  assert.equal(pulse.tone, 'amber');
  assert.ok(pulse.why.length > 0, 'why must never be blank, even with no narrative');
  assert.equal(pulse.signals.length, 0);
  assert.equal(pulse.context.length, 0);
});

console.log(`\n${checks} checks passed.`);
