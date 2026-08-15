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
import { HERO_STUDENT_NAMES } from '../api/mock';
import { getPulse, hasAuthoredPulse, pulseTone, type PulseTone } from './pulse';

let checks = 0;
function check(label: string, run: () => void): void {
  run();
  checks += 1;
  console.log(`  ✓ ${label}`);
}

const TONES: PulseTone[] = ['red', 'amber', 'green'];

check('Maya Okonkwo reads red — the intervention case', () => {
  assert.equal(getPulse('Maya Okonkwo').tone, 'red');
  assert.equal(pulseTone('Maya Okonkwo'), 'red');
});

check('Priya Raghunathan reads red — 6 unexamined AI offloads', () => {
  assert.equal(getPulse('Priya Raghunathan').tone, 'red');
  assert.equal(pulseTone('Priya Raghunathan'), 'red');
});

check('pulseTone agrees with getPulse().tone', () => {
  for (const name of [...HERO_STUDENT_NAMES, 'Nobody Really']) {
    assert.equal(pulseTone(name), getPulse(name).tone);
  }
});

check('every hero pulse is well-formed', () => {
  for (const name of HERO_STUDENT_NAMES) {
    const pulse = getPulse(name);
    assert.ok(TONES.includes(pulse.tone), `bad tone for ${name}`);
    assert.ok(pulse.headline.length > 0, `no headline for ${name}`);
    assert.ok(pulse.why.length > 0, `no why for ${name}`);
    assert.ok(pulse.signals.length >= 1, `no signals for ${name}`);
    assert.ok(pulse.context.length >= 1, `no context for ${name}`);
    assert.ok(pulse.since.changes.length >= 1, `no changes for ${name}`);
    for (const s of pulse.signals) {
      assert.ok(['up', 'down', 'flat'].includes(s.trend), `bad trend for ${name}`);
    }
  }
});

check('an unknown student falls back to a steady green', () => {
  const pulse = getPulse('Nobody Really');
  assert.equal(pulse.tone, 'green');
  assert.ok(pulse.signals.length >= 1);
});

// Guards the fix in PassportPanel/StudentSidebar: the six story-arc students
// must never hand off to a live digest, even once ordinary AI-tutor activity
// starts showing up for them on the deployed app.
check('every hero student has an authored pulse to pin to', () => {
  for (const name of HERO_STUDENT_NAMES) {
    assert.equal(hasAuthoredPulse(name), true, `${name} should be pinned to its authored pulse`);
  }
  assert.equal(hasAuthoredPulse('Nobody Really'), false);
});

console.log(`\n${checks} checks passed.`);
