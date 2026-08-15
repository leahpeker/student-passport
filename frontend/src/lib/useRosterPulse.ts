import { useCallback, useMemo } from 'react';
import { getDigest } from '../api/client';
import type { Student } from '../api/types';
import { useAsync } from './useAsync';
import { getPulse, pulseFromDigest, type Pulse } from './pulse';

/**
 * The full pulse for one student. Real when the backend has a computed
 * digest for this viewer (teacher only — see `getDigest`); the authored
 * fixture otherwise, so a guardian, a student, or a still-loading row never
 * renders as broken or missing. Shared by anything that renders one
 * student's own dot/card (the sidebar); `useClassroomPulses` below is the
 * equivalent for a whole roster that needs to bucket by tone before it can
 * render at all.
 */
export function usePulse(studentId: number, firstName = ''): Pulse {
  const load = useCallback(() => getDigest(studentId), [studentId]);
  const { data: digest } = useAsync(load);
  return digest ? pulseFromDigest(digest, firstName) : getPulse(studentId);
}

/**
 * Pulses for a whole roster, keyed by student id. Grouping students by tone
 * has to know every tone before it can lay out sections, so this fetches the
 * roster's digests together rather than one hook per card (the pattern
 * `usePulse`/`RosterDot` use, which suits a flat list but can't drive a
 * bucketed layout).
 *
 * Starts from the authored fixture for every student — same silent fallback
 * as `usePulse` — so the roster buckets immediately instead of blocking on
 * the network, then re-buckets once real digests are in.
 */
export function useClassroomPulses(students: Student[]): Record<number, Pulse> {
  const ids = students.map((s) => s.id).join(',');
  const fixture = useMemo(
    () => Object.fromEntries(students.map((s) => [s.id, getPulse(s.id)])),
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `ids` is the real dependency; `students` is re-created every render.
    [ids],
  );
  const load = useCallback(async () => {
    const entries = await Promise.all(
      students.map(async (s) => {
        const digest = await getDigest(s.id);
        return [s.id, digest ? pulseFromDigest(digest, s.first_name) : getPulse(s.id)] as const;
      }),
    );
    return Object.fromEntries(entries);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- see above.
  }, [ids]);
  const { data } = useAsync(load);
  // `useAsync` doesn't clear `data` when `load` changes, so right after
  // switching classrooms `data` can still be the previous roster's map —
  // stale, and missing entries for the new one. Only trust it once it
  // actually covers every student currently being rendered.
  if (data && students.every((s) => s.id in data)) return data;
  return fixture;
}
