/**
 * What a signed-in role may reach and see.
 *
 * The server is the real boundary: the API gates every student-scoped
 * endpoint with `can_view_student` and answers 404 — never 403 — so it does
 * not confirm a student exists. These helpers exist so the UI does not offer
 * or render what the server would refuse.
 */

import type { Me, Role, StudentRecord } from '../api/types';

/** Which landing view a role starts in. */
export function landingPath(me: Me): string {
  if (me.role === 'teacher') return '/teacher';
  if (me.role === 'guardian') return '/guardian';
  if (me.student_id != null) return `/students/${me.student_id}`;
  return '/';
}

/**
 * Whether this user may open a student's passport. `me.students` is the set
 * the server says is reachable: a teacher's roster, a guardian's wards, or a
 * student themselves.
 */
export function canViewStudent(me: Me, studentId: number): boolean {
  return me.students.some((student) => student.id === studentId);
}

/**
 * Record sources a role never sees. A student does not read teacher
 * observations or behaviour entries about themselves — a note about what is
 * happening at a student's home reads very differently to the student it is
 * about. The API strips these too; this keeps the UI from rendering an empty
 * section where one was removed.
 */
const HIDDEN_FROM: Partial<Record<Role, ReadonlySet<StudentRecord['source']>>> = {
  student: new Set(['behavior', 'observation'] as const),
};

export function hiddenSources(role: Role): ReadonlySet<StudentRecord['source']> {
  return HIDDEN_FROM[role] ?? new Set();
}

/** Whether the behaviour section should render at all for this role. */
export function showsBehavior(role: Role): boolean {
  return !hiddenSources(role).has('behavior');
}
