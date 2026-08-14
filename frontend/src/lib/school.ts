/**
 * School calendar facts and the derivations the charts are built from.
 *
 * This is presentation logic over records the client has already fetched, not
 * a second source of data. Nothing here reads the network or the fixtures.
 */

import type { StudentRecord } from '../api/types';

/** School year 2025-09-02 to 2026-06-05. */
export const YEAR_START_MS = Date.UTC(2025, 8, 2);
export const YEAR_END_MS = Date.UTC(2026, 5, 5);

/** Month index 0 is September, 9 is June. */
export const MONTH_LABELS = [
  'Sep',
  'Oct',
  'Nov',
  'Dec',
  'Jan',
  'Feb',
  'Mar',
  'Apr',
  'May',
  'Jun',
];

/** Period 1 to 7. Lunch falls between period 4 and period 5. */
export const PERIODS = [1, 2, 3, 4, 5, 6, 7];

export const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

/** Month index for an ISO date, 0 = September. */
export function monthOf(iso: string): number {
  const d = new Date(`${iso}T00:00:00Z`);
  return (d.getUTCFullYear() - 2025) * 12 + d.getUTCMonth() - 8;
}

/** Weekday name for an ISO date, e.g. "Monday". */
export function weekdayOf(iso: string): string {
  return new Date(`${iso}T00:00:00Z`).toLocaleDateString('en-US', {
    weekday: 'long',
    timeZone: 'UTC',
  });
}

/** "12 Nov 2025". */
export function formatDate(iso: string): string {
  return new Date(`${iso}T00:00:00Z`).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  });
}

/** Reads a number out of a record's untyped `data` bag. */
export function numberField(record: StudentRecord, key: string): number | null {
  const value = record.data[key];
  return typeof value === 'number' ? value : null;
}

/** Reads a string out of a record's untyped `data` bag. */
export function stringField(record: StudentRecord, key: string): string | null {
  const value = record.data[key];
  return typeof value === 'string' ? value : null;
}

function mean(xs: number[]): number {
  return xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0;
}

// ---------------------------------------------------------------------------
// Derivations
// ---------------------------------------------------------------------------

/** One row per month, one column per subject. Missing months are omitted. */
export interface PerformancePoint {
  month: string;
  [subject: string]: string | number;
}

export interface PerformanceSeries {
  subjects: string[];
  points: PerformancePoint[];
  /** Change from the first month to the last, per subject. */
  change: Record<string, number>;
}

export function performanceOverTime(records: StudentRecord[]): PerformanceSeries {
  const assessments = records.filter((r) => r.source === 'assessment');
  const subjects = [
    ...new Set(assessments.map((r) => stringField(r, 'subject') ?? 'Unknown')),
  ].sort();

  const byMonth = new Map<number, Map<string, number[]>>();
  for (const record of assessments) {
    const score = numberField(record, 'score');
    if (score == null) continue;
    const month = monthOf(record.date);
    if (month < 0 || month >= MONTH_LABELS.length) continue;
    const subject = stringField(record, 'subject') ?? 'Unknown';
    const row = byMonth.get(month) ?? new Map<string, number[]>();
    row.set(subject, [...(row.get(subject) ?? []), score]);
    byMonth.set(month, row);
  }

  const points: PerformancePoint[] = [];
  for (let m = 0; m < MONTH_LABELS.length; m++) {
    const row = byMonth.get(m);
    if (!row) continue;
    const point: PerformancePoint = { month: MONTH_LABELS[m] };
    for (const subject of subjects) {
      const scores = row.get(subject);
      if (scores) point[subject] = Math.round(mean(scores));
    }
    points.push(point);
  }

  const change: Record<string, number> = {};
  for (const subject of subjects) {
    const values = points
      .map((p) => p[subject])
      .filter((v): v is number => typeof v === 'number');
    change[subject] = values.length > 1 ? values[values.length - 1] - values[0] : 0;
  }

  return { subjects, points, change };
}

export interface EngagementPoint {
  period: string;
  rating: number;
  samples: number;
}

/** Mean engagement rating per period — the "when are they most engaged" view. */
export function engagementByPeriod(records: StudentRecord[]): EngagementPoint[] {
  const byPeriod = new Map<number, number[]>();
  for (const record of records) {
    if (record.source !== 'engagement') continue;
    const period = numberField(record, 'period');
    const rating = numberField(record, 'rating');
    if (period == null || rating == null) continue;
    byPeriod.set(period, [...(byPeriod.get(period) ?? []), rating]);
  }
  return PERIODS.filter((p) => byPeriod.has(p)).map((period) => {
    const ratings = byPeriod.get(period) ?? [];
    return {
      period: `Period ${period}`,
      rating: Number(mean(ratings).toFixed(2)),
      samples: ratings.length,
    };
  });
}

export interface BehaviorPoint {
  month: string;
  incidents: number;
}

/** Behaviour entries per month, zero-filled so gaps read as gaps. */
export function behaviorOverTime(records: StudentRecord[]): BehaviorPoint[] {
  const counts = new Array<number>(MONTH_LABELS.length).fill(0);
  for (const record of records) {
    if (record.source !== 'behavior') continue;
    const month = monthOf(record.date);
    if (month >= 0 && month < counts.length) counts[month] += 1;
  }
  return MONTH_LABELS.map((month, i) => ({ month, incidents: counts[i] }));
}

/** Absences per weekday, used to surface a day-of-week pattern. */
export function absencesByWeekday(records: StudentRecord[]): Record<string, number> {
  const counts: Record<string, number> = Object.fromEntries(
    WEEKDAYS.map((d) => [d, 0]),
  );
  for (const record of records) {
    if (record.source !== 'attendance') continue;
    if (stringField(record, 'status') !== 'absent') continue;
    const day = weekdayOf(record.date);
    if (day in counts) counts[day] += 1;
  }
  return counts;
}

/** Which periods behaviour entries fall in. */
export function behaviorByPeriod(records: StudentRecord[]): Record<number, number> {
  const counts: Record<number, number> = {};
  for (const period of PERIODS) counts[period] = 0;
  for (const record of records) {
    if (record.source !== 'behavior') continue;
    const period = numberField(record, 'period');
    if (period != null && period in counts) counts[period] += 1;
  }
  return counts;
}
