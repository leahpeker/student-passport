import { useCallback, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { getClassrooms } from '../../api/client';
import type { Classroom, Me, Student } from '../../api/types';
import { useAsync } from '../../lib/useAsync';
import { pulseTone } from '../../lib/pulse';
import { toneDot } from './tone';

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
  const [collapsed, setCollapsed] = useState(false);

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

  if (collapsed) {
    return (
      <CollapsedRail
        groups={groups}
        activeStudentId={activeStudentId}
        onExpand={() => setCollapsed(false)}
      />
    );
  }

  return (
    <nav
      aria-label="Students"
      className="sticky top-4 flex max-h-[calc(100vh-120px)] flex-col overflow-y-auto rounded-lg bg-surface p-3 elev-sm"
    >
      <div className="mb-2 flex items-center justify-between px-1">
        <span className="text-[10.5px] font-medium tracking-[0.1em] text-muted uppercase">
          {isTeacher ? 'Your classrooms' : 'Passport'}
        </span>
        <button
          type="button"
          onClick={() => setCollapsed(true)}
          aria-label="Collapse the roster"
          className="btn btn-secondary px-2 py-1 text-[12px]"
        >
          ‹
        </button>
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
                  <span
                    aria-hidden="true"
                    className={`h-2 w-2 shrink-0 rounded-full ${toneDot[pulseTone(student.id)]}`}
                  />
                  <span
                    className={`truncate text-[12.5px] ${active ? 'font-medium text-text' : 'text-text/85'}`}
                  >
                    {student.name}
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

/** The thin dots-only rail shown when the roster is collapsed. */
function CollapsedRail({
  groups,
  activeStudentId,
  onExpand,
}: {
  groups: { students: Student[] }[];
  activeStudentId: number;
  onExpand: () => void;
}) {
  const students = groups.flatMap((g) => g.students);
  return (
    <nav
      aria-label="Students"
      className="sticky top-4 flex flex-col items-center gap-3 rounded-lg bg-surface py-3 elev-sm"
    >
      <button
        type="button"
        onClick={onExpand}
        aria-label="Expand the roster"
        className="btn btn-secondary px-2 py-1 text-[12px]"
      >
        ›
      </button>
      {students.map((student) => {
        const active = student.id === activeStudentId;
        return (
          <Link
            key={student.id}
            to={`/students/${student.id}`}
            aria-label={student.name}
            title={student.name}
            aria-current={active ? 'page' : undefined}
            className="grid place-items-center"
          >
            <span
              className={`h-2.5 w-2.5 rounded-full ${toneDot[pulseTone(student.id)]} ${
                active ? 'ring-2 ring-accent ring-offset-2 ring-offset-surface' : ''
              }`}
            />
          </Link>
        );
      })}
    </nav>
  );
}
