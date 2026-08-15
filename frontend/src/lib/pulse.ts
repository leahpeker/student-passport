/**
 * The daily/weekly "pulse" — a red / amber / green read on where a student is,
 * with the signals and context behind it.
 *
 * `getPulse`/`pulseTone` are an authored fixture for the six hero students and
 * a steady-green default for everyone else — used only by the mock data layer
 * (`api/mock.ts`) so the demo still looks intentional with `VITE_USE_MOCKS`.
 * Real callers use `pulseFromDigest`, which builds the same `Pulse` shape from
 * the backend's actual one-day triage (`GET /students/<id>/digest/`) — the
 * only real signal the backend computes today. That triage covers app-tutor
 * activity alone, so it is a narrower read than the fixture's "wellbeing /
 * attendance / grades" framing implies; widening it to a genuinely holistic
 * weekly pulse is backend work, not done here.
 */

import type { Digest, DigestAction } from '../api/types';

export type PulseTone = 'red' | 'amber' | 'green';

export type Trend = 'up' | 'down' | 'flat';

/** One driver behind the status. `concerning` flips the trend arrow red. */
export interface PulseSignal {
  label: string;
  detail: string;
  trend: Trend;
  /** True when this trend is the worrying direction for this student. */
  concerning: boolean;
}

/** Something that moved since the reader last opened this passport. */
export interface PulseChange {
  direction: 'up' | 'down' | 'new';
  text: string;
}

/** A framing metric — progress vs. previous, standing vs. benchmark, etc. */
export interface PulseContext {
  label: string;
  value: string;
  tone: 'good' | 'bad' | 'neutral';
}

export interface Pulse {
  tone: PulseTone;
  /** The one-word-ish status, e.g. "Needs intervention" / "On track". */
  headline: string;
  /** The trend line under the headline, e.g. "Down 3 weeks". */
  trendNote: string;
  /** A short standing "why" — semi-permanent context, not today's blip. */
  why: string;
  since: { asOf: string; changes: PulseChange[] };
  signals: PulseSignal[];
  context: PulseContext[];
}

const PULSES: Record<number, Pulse> = {
  // 1 — Maya Okonkwo: high achiever burning out. The intervention showcase.
  1: {
    tone: 'red',
    headline: 'Needs intervention',
    trendNote: 'Wellbeing down 3 weeks',
    why: 'Top work, rising cost — late nights, self-criticism, and pulling back in class. Grades are steady; everything around the work is not.',
    since: {
      asOf: 'Aug 8',
      changes: [
        { direction: 'up', text: '2 more late-night AI-tutor sessions (now most nights)' },
        { direction: 'down', text: 'Asked 0 questions in class this week' },
        { direction: 'new', text: 'New guardian note added about sleep' },
      ],
    },
    signals: [
      { label: 'Sleep / late-night work', detail: 'Active in the AI tutor past midnight, most nights', trend: 'up', concerning: true },
      { label: 'Self-directed anxiety', detail: 'Apologising for work that needs no apology', trend: 'up', concerning: true },
      { label: 'Class participation', detail: 'Asking fewer questions than in September', trend: 'down', concerning: true },
    ],
    context: [
      { label: 'Grades', value: 'Steady', tone: 'good' },
      { label: 'vs. state benchmark', value: 'Above', tone: 'good' },
      { label: 'Engagement', value: 'Falling', tone: 'bad' },
      { label: 'Wellbeing', value: 'Down 3 wks', tone: 'bad' },
    ],
  },
  // 2 — Deshawn Carter: capable, but mornings and Mondays are hard.
  2: {
    tone: 'amber',
    headline: 'Watch',
    trendNote: 'Attendance pattern, not ability',
    why: 'Strong work on the days he is in the room. The week starts badly and mornings are harder than afternoons.',
    since: {
      asOf: 'Aug 8',
      changes: [
        { direction: 'down', text: 'Missed another Monday first period' },
        { direction: 'up', text: 'Led his table group again in 6th period' },
      ],
    },
    signals: [
      { label: 'Monday attendance', detail: 'Most absences land on a Monday', trend: 'down', concerning: true },
      { label: 'Morning engagement', detail: 'Low through 4th period, sharp rise after lunch', trend: 'flat', concerning: false },
      { label: 'Grades', detail: 'Climbing steadily when present', trend: 'up', concerning: false },
    ],
    context: [
      { label: 'Grades', value: 'Rising', tone: 'good' },
      { label: 'Attendance', value: '9 Mon absences', tone: 'bad' },
      { label: 'Afternoon engagement', value: 'High', tone: 'good' },
    ],
  },
  // 3 — Alina Restrepo: newcomer closing the reading gap fast.
  3: {
    tone: 'green',
    headline: 'On track',
    trendNote: 'Strongest reading gain in her year',
    why: 'Arrived with little classroom English and has closed most of the reading gap in a year. Maths was never the barrier.',
    since: {
      asOf: 'Aug 8',
      changes: [
        { direction: 'up', text: 'Reading score up again this month' },
        { direction: 'new', text: 'Translated for a classmate, unprompted' },
      ],
    },
    signals: [
      { label: 'Reading growth', detail: 'Low 50s in September to low 80s by June', trend: 'up', concerning: false },
      { label: 'Group work', detail: 'Most engaged in pairs and lab periods', trend: 'up', concerning: false },
    ],
    context: [
      { label: 'Reading', value: 'Climbing', tone: 'good' },
      { label: 'Maths', value: 'In the 90s', tone: 'good' },
      { label: 'Behaviour', value: 'Clear', tone: 'good' },
    ],
  },
  // 4 — Jordan Whitaker: format-dependent; referrals cluster in lectures.
  4: {
    tone: 'amber',
    headline: 'Watch',
    trendNote: 'Format, not content',
    why: 'Runs the lab bench and helps other groups; loses attention in long lecture blocks. The 504 plan allows movement breaks.',
    since: {
      asOf: 'Aug 8',
      changes: [
        { direction: 'down', text: 'Two referrals in 3rd-period lecture' },
        { direction: 'up', text: 'Ran the water-quality bench solo for a full period' },
      ],
    },
    signals: [
      { label: 'Lecture-block referrals', detail: 'Cluster in the two long lecture periods', trend: 'flat', concerning: true },
      { label: 'Practical work', detail: 'Near the top of the class hands-on', trend: 'up', concerning: false },
      { label: 'Timed tests', detail: '~30-point gap vs. project work', trend: 'down', concerning: true },
    ],
    context: [
      { label: 'Projects', value: 'Mid 90s', tone: 'good' },
      { label: 'Timed tests', value: 'Low 60s', tone: 'bad' },
      { label: 'Lab periods', value: 'Incident-free', tone: 'good' },
    ],
  },
  // 5 — Sam Nakamura: mid-year transfer dip, now recovering.
  5: {
    tone: 'amber',
    headline: 'Watch',
    trendNote: 'Recovering since the transfer',
    why: 'A quiet mid-year transfer. Grades dipped across the board, then started climbing back before any formal intervention.',
    since: {
      asOf: 'Aug 8',
      changes: [
        { direction: 'up', text: 'First unprompted contribution of the year' },
        { direction: 'up', text: 'Scores back into the high 70s' },
      ],
    },
    signals: [
      { label: 'Post-transfer engagement', detail: 'Flat drop across every class, now lifting', trend: 'up', concerning: false },
      { label: 'Social connection', detail: 'Eats alone; two classmates spoke to him this week', trend: 'up', concerning: true },
      { label: 'Sequencing gap', detail: 'Behind on the order, not the thinking', trend: 'flat', concerning: true },
    ],
    context: [
      { label: 'Grades', value: 'Recovering', tone: 'good' },
      { label: 'Participation', value: 'Low but rising', tone: 'neutral' },
      { label: 'Behaviour', value: 'Clear', tone: 'good' },
    ],
  },
  // 6 — Priya Raghunathan: gifted; top tests, floor-level homework.
  6: {
    tone: 'amber',
    headline: 'Watch',
    trendNote: 'Under-challenged, not underperforming',
    why: 'Top of every test, bottom of every homework list — she will not repeat practice she considers already learned. The advanced-learner plan is unactioned.',
    since: {
      asOf: 'Aug 8',
      changes: [
        { direction: 'down', text: 'Two more homework sets not handed in' },
        { direction: 'up', text: 'Arrived early to studio again' },
      ],
    },
    signals: [
      { label: 'Homework completion', detail: 'Scores in the 40s and 50s', trend: 'down', concerning: true },
      { label: 'Academic engagement', detail: 'Low and flat outside her elective', trend: 'flat', concerning: true },
      { label: 'Gifted plan', detail: 'Eligible for acceleration, not yet actioned', trend: 'flat', concerning: true },
    ],
    context: [
      { label: 'Test scores', value: 'Mid-high 90s', tone: 'good' },
      { label: 'Homework', value: '40s–50s', tone: 'bad' },
      { label: 'Elective', value: 'Fully engaged', tone: 'good' },
    ],
  },
};

/** A steady, unremarkable read — the default until a real feed says otherwise. */
function defaultPulse(): Pulse {
  return {
    tone: 'green',
    headline: 'On track',
    trendNote: 'No pattern needs attention',
    why: 'A steady presence across every source. Work comes in on time and the standard holds across the year.',
    since: { asOf: 'Aug 8', changes: [{ direction: 'up', text: 'Nothing notable has changed' }] },
    signals: [
      { label: 'Engagement', detail: 'Even across the timetable', trend: 'flat', concerning: false },
      { label: 'Grades', detail: 'Narrow band, mild upward trend', trend: 'up', concerning: false },
    ],
    context: [
      { label: 'Grades', value: 'Steady', tone: 'good' },
      { label: 'Behaviour', value: 'Clear', tone: 'good' },
    ],
  };
}

/** The full pulse for a student. Authored for heroes, steady-green otherwise. */
export function getPulse(studentId: number): Pulse {
  return PULSES[studentId] ?? defaultPulse();
}

/** Just the colour — cheap enough to call per roster row for the nav dots. */
export function pulseTone(studentId: number): PulseTone {
  return (PULSES[studentId] ?? { tone: 'green' as const }).tone;
}

// Mirrors passport/narrative.py's ACCURACY_CONCERN / ACCURACY_WATCH exactly —
// context coloring should agree with the thresholds that produced the flags.
const ACCURACY_CONCERN = 0.5;
const ACCURACY_WATCH = 0.7;

const ACTION_TONE: Record<DigestAction, PulseTone> = {
  intervene: 'red',
  check_in: 'amber',
  celebrate: 'green',
};

const ACTION_HEADLINE: Record<DigestAction, string> = {
  intervene: 'Needs intervention',
  check_in: 'Check in',
  celebrate: 'On track',
};

/**
 * The real-data path. Turns one day's computed triage from the backend
 * (`GET /students/<id>/digest/`) into the same `Pulse` shape the UI already
 * renders — `action` decides the tone, `flags` become signals, `topics`
 * become context. Nothing here re-judges what the backend already decided.
 */
export function pulseFromDigest(digest: Digest, firstName: string): Pulse {
  const tone = ACTION_TONE[digest.action];
  return {
    tone,
    headline: ACTION_HEADLINE[digest.action],
    trendNote: digest.headline,
    why: digest.narrative || digest.headline || `No recent app activity on file for ${firstName}.`,
    since: {
      asOf: digest.date ?? 'unknown',
      changes: (digest.insights ?? []).map((text) => ({ direction: 'new' as const, text })),
    },
    signals: digest.flags.map((flag) => ({
      label: `${flag.topic} (${flag.kind})`,
      detail: flag.detail,
      trend: flag.kind === 'pace' ? 'down' : 'flat',
      concerning: true,
    })),
    context: digest.topics.map((t) => ({
      label: t.topic,
      value: `${t.correct}/${t.attempted}`,
      tone: t.accuracy < ACCURACY_CONCERN ? 'bad' : t.accuracy < ACCURACY_WATCH ? 'neutral' : 'good',
    })),
  };
}
