import { useCallback, useState } from 'react';
import { Link } from 'react-router-dom';
import { getClassrooms } from '../api/client';
import type { Classroom, Student } from '../api/types';
import { AsyncState } from '../components/AsyncState';
import { Tabs } from '../components/Tabs';
import { useAsync } from '../lib/useAsync';

function initialsOf(student: Student): string {
  return `${student.first_name[0] ?? ''}${student.last_name[0] ?? ''}`.toUpperCase();
}

function Roster({ classroom }: { classroom: Classroom }) {
  return (
    <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {classroom.students.map((student: Student) => (
        <li key={student.id}>
          <Link
            to={`/students/${student.id}`}
            className="card elev-sm block h-full transition-colors hover:bg-neutral-800/40"
          >
            <div className="flex items-center gap-2.5">
              <span aria-hidden="true" className="avatar h-7 w-7 text-[11px]">
                {initialsOf(student)}
              </span>
              <span className="truncate text-[13.5px] font-medium text-text">
                {student.name}
              </span>
            </div>
            <span className="text-[11px] text-muted">
              Grade {student.grade} · {student.pronouns}
            </span>
            <span className="mt-1 text-[12px] font-medium text-accent">
              Open passport
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}

export function TeacherView() {
  const load = useCallback(() => getClassrooms(), []);
  const { data, error, loading } = useAsync(load);
  const [activeId, setActiveId] = useState<string | null>(null);

  if (loading || error) {
    return <AsyncState loading={loading} error={error} label="your classrooms" />;
  }
  if (!data || data.length === 0) {
    return <p className="text-muted">You do not teach any classrooms yet.</p>;
  }

  const active = data.find((c) => String(c.id) === activeId) ?? data[0];

  return (
    <div>
      <h1 className="text-[26px] font-medium tracking-[-0.02em] text-text">
        Your classrooms
      </h1>
      <p className="mt-2 mb-6 text-[13.5px] leading-relaxed text-muted">
        Pick a class, then open a student to see everything the school already
        knows about them in one place.
      </p>

      <Tabs
        label="Classrooms"
        tabs={data.map((c) => ({
          id: String(c.id),
          label: c.name,
          hint: `Period ${c.period} · ${c.students.length} students`,
        }))}
        activeId={String(active.id)}
        onChange={setActiveId}
      >
        <h2 className="sr-only">{active.name} roster</h2>
        <Roster classroom={active} />
      </Tabs>
    </div>
  );
}
