/**
 * Plain assert checks over the pulse fixtures. No test framework.
 *
 *   npx tsx src/lib/pulse.test.ts
 *
 * These guard the intervention showcase: if Maya stops reading red, or a hero
 * pulse loses its signals, the redesigned passport header says the wrong thing
 * about where a student is.
 */

import assert from 'node:assert/strict';
import { HERO_STUDENT_IDS } from '../api/mock';
import { getPulse, pulseTone, type PulseTone } from './pulse';

let checks = 0;
function check(label: string, run: () => void): void {
  run();
  checks += 1;
  console.log(`  ✓ ${label}`);
}

const TONES: PulseTone[] = ['red', 'amber', 'green'];

check('Maya (1) reads red — the intervention case', () => {
  assert.equal(getPulse(1).tone, 'red');
  assert.equal(pulseTone(1), 'red');
});

check('pulseTone agrees with getPulse().tone', () => {
  for (const id of [...HERO_STUDENT_IDS, 999]) {
    assert.equal(pulseTone(id), getPulse(id).tone);
  }
});

check('every hero pulse is well-formed', () => {
  for (const id of HERO_STUDENT_IDS) {
    const pulse = getPulse(id);
    assert.ok(TONES.includes(pulse.tone), `bad tone for ${id}`);
    assert.ok(pulse.headline.length > 0, `no headline for ${id}`);
    assert.ok(pulse.why.length > 0, `no why for ${id}`);
    assert.ok(pulse.signals.length >= 1, `no signals for ${id}`);
    assert.ok(pulse.context.length >= 1, `no context for ${id}`);
    assert.ok(pulse.since.changes.length >= 1, `no changes for ${id}`);
    for (const s of pulse.signals) {
      assert.ok(['up', 'down', 'flat'].includes(s.trend), `bad trend for ${id}`);
    }
  }
});

check('an unknown student falls back to a steady green', () => {
  const pulse = getPulse(4242);
  assert.equal(pulse.tone, 'green');
  assert.ok(pulse.signals.length >= 1);
});

console.log(`\n${checks} checks passed.`);
