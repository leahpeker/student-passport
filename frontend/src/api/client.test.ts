/**
 * Plain assert checks over the fixture data. No test framework.
 *
 *   npm test        (npx tsx src/api/client.test.ts)
 *
 * These guard the demo: if a hero student loses their narrative, their scores
 * or their engagement samples, the passport page renders empty sections and
 * the charts have nothing to draw.
 */

import assert from 'node:assert/strict';
import { HERO_STUDENT_IDS, passportFor, recordsFor } from './mock';
import { engagementByPeriod, performanceOverTime } from '../lib/school';
import type { RecordSource } from './types';

let checks = 0;

function check(label: string, run: () => void): void {
  run();
  checks += 1;
  console.log(`  ok  ${label}`);
}

assert.equal(HERO_STUDENT_IDS.length, 6, 'expected six hero students');

for (const id of HERO_STUDENT_IDS) {
  const passport = passportFor(id);
  assert.ok(passport, `no passport for student ${id}`);
  const who = passport.student.name;
  const records = recordsFor(id);

  check(`${who} — overview has all three voices`, () => {
    const { teacher_voice, guardian_voice, student_voice } = passport.sections.overview;
    for (const voice of [teacher_voice, guardian_voice, student_voice]) {
      assert.ok(voice.trim().length > 40, 'a voice in the overview is empty');
    }
    assert.ok(passport.sections.how_they_learn.trim().length > 40);
  });

  check(`${who} — has assessment records that chart`, () => {
    const assessments = records.filter((r) => r.source === 'assessment');
    assert.ok(assessments.length >= 1, 'no assessment records');
    for (const record of assessments) {
      assert.equal(typeof record.data.score, 'number');
      assert.equal(typeof record.data.subject, 'string');
    }
    const { points, subjects } = performanceOverTime(records);
    assert.ok(points.length >= 2, 'performance chart needs at least two months');
    assert.ok(subjects.length >= 1);
  });

  check(`${who} — has engagement records that chart`, () => {
    const engagement = records.filter((r) => r.source === 'engagement');
    assert.ok(engagement.length >= 1, 'no engagement records');
    for (const record of engagement) {
      const rating = record.data.rating;
      const period = record.data.period;
      assert.equal(typeof period, 'number');
      assert.ok(typeof rating === 'number' && rating >= 1 && rating <= 5);
    }
    assert.ok(engagementByPeriod(records).length >= 1);
  });

  check(`${who} — spans at least six sources`, () => {
    const sources = new Set<RecordSource>(records.map((r) => r.source));
    assert.ok(sources.size >= 6, `only ${sources.size} sources`);
    assert.ok(!sources.has('question'), 'questions are written at runtime only');
  });

  check(`${who} — every date is a school-year weekday`, () => {
    for (const record of records) {
      assert.match(record.date, /^\d{4}-\d{2}-\d{2}$/);
      assert.ok(record.date >= '2025-09-02' && record.date <= '2026-06-05');
      const weekday = new Date(`${record.date}T00:00:00Z`).getUTCDay();
      assert.ok(weekday >= 1 && weekday <= 5, `${record.date} is a weekend`);
    }
  });
}

console.log(`\n${checks} checks passed.`);
