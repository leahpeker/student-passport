import { useCallback, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { getClassrooms, getDigest } from '../../api/client';
import type { Classroom, Me, Student } from '../../api/types';
import { useAsync } from '../../lib/useAsync';
import { hasDigestActivity, pulseFromDigest, pulseTone, type PulseTone } from '../../lib/pulse';
import { toneDot } from './tone';
import { AiBadge } from '../AiBadge';

/**
 * The dot's colour for one roster row. Real when the backend has a digest with
 * actual activity behind it (teacher only — see `getDigest`); the authored
 * fixture otherwise, so a guardian, a student, a still-loading row, or a
 * student with no app activity on file never renders as a broken, missing, or
 * falsely amber dot. The fallback is keyed by name rather than id — see
 * `lib/pulse.ts` for why an id misses against the real API.
 */
function useRosterTone(studentId: number, studentName: string): PulseTone {
  const load = useCallback(() => getDigest(studentId), [studentId]);
  const { data: digest } = useAsync(load);
  return hasDigestActivity(digest) ? pulseFromDigest(digest, '').tone : pulseTone(studentName);
}

/** One roster dot. Its own component so `useRosterTone` gets one hook
 * instance per student rather than being called inside a `.map()`. */
function RosterDot({
  studentId,
  studentName,
  className,
}: {
  studentId: number;
  studentName: string;
  className: string;
}) {
  const tone = useRosterTone(studentId, studentName);
  return <span aria-hidden="true" className={`${className} ${toneDot[tone]}`} />;
}

/**
 * A persistent roster rail. It lets a teacher move between students — and
 * between classes — without going back to the homepage, and puts a pulse dot
 * beside every name so a red student is visible before you open them.
 *
 * Teachers see their classes as collapsible groups; a guardian or student sees
 * the flat set of students they can reach.
 */
export function StudentSidebar({
  me,
  activeStudentId,
}: {
  me: Me;
  activeStudentId: number;
}) {
  const isTeacher = me.role === 'teacher';
  const load = useCallback(
    () => (isTeacher ? getClassrooms() : Promise.resolve<Classroom[]>([])),
    [isTeacher],
  );
  const { data: classrooms } = useAsync(load);

  // Non-teachers get one flat group; teachers get a group per class.
  const groups = useMemo(() => {
    if (isTeacher && classrooms) {
      return classrooms.map((c) => ({
        id: String(c.id),
        title: c.name,
        hint: `Period ${c.period}`,
        students: c.students,
      }));
    }
    return [{ id: 'mine', title: 'Your students', hint: '', students: me.students }];
  }, [isTeacher, classrooms, me.students]);

  return (
    <nav
      aria-label="Students"
      className="sticky top-4 flex max-h-[calc(100vh-120px)] flex-col overflow-y-auto rounded-lg bg-surface p-3 elev-sm"
    >
      <div className="mb-2 px-1">
        <span className="text-[10.5px] font-medium tracking-[0.1em] text-muted uppercase">
          {isTeacher ? 'Your classrooms' : 'Passport'}
        </span>
      </div>

      {groups.map((group) => (
        <SidebarGroup
          key={group.id}
          title={group.title}
          hint={group.hint}
          students={group.students}
          activeStudentId={activeStudentId}
          startOpen={
            groups.length === 1 ||
            group.students.some((s) => s.id === activeStudentId)
          }
        />
      ))}
    </nav>
  );
}

function SidebarGroup({
  title,
  hint,
  students,
  activeStudentId,
  startOpen,
}: {
  title: string;
  hint: string;
  students: Student[];
  activeStudentId: number;
  startOpen: boolean;
}) {
  const [open, setOpen] = useState(startOpen);

  return (
    <div className="mb-1.5">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left hover:bg-neutral-800/40"
      >
        <span aria-hidden="true" className="w-2 text-[10px] text-muted">
          {open ? '▾' : '▸'}
        </span>
        <span className="flex-1 truncate text-[12.5px] font-medium text-text">
          {title}
        </span>
        {hint && <span className="text-[10.5px] text-muted">{hint}</span>}
      </button>

      {open && (
        <ul className="mt-0.5 mb-1 space-y-0.5 pl-1.5">
          {students.map((student) => {
            const active = student.id === activeStudentId;
            return (
              <li key={student.id}>
                <Link
                  to={`/students/${student.id}`}
                  aria-current={active ? 'page' : undefined}
                  className={`flex items-center gap-2.5 rounded-md px-2 py-1.5 transition-colors ${
                    active
                      ? 'bg-neutral-800/60 shadow-[inset_2px_0_0_var(--color-accent)]'
                      : 'hover:bg-neutral-800/40'
                  }`}
                >
                  <RosterDot
                    studentId={student.id}
                    studentName={student.name}
                    className="h-2 w-2 shrink-0 rounded-full"
                  />
                  <span
                    className={`truncate text-[12.5px] ${active ? 'font-medium text-text' : 'text-text/85'}`}
                  >
                    {student.name}
                  </span>
                  {student.has_ai_analysis && <AiBadge />}
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

