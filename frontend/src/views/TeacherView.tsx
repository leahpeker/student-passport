import { useCallback, useState } from 'react';
import { Link } from 'react-router-dom';
import { getClassrooms } from '../api/client';
import type { Classroom, Student } from '../api/types';
import { AsyncState } from '../components/AsyncState';
import { Tabs } from '../components/Tabs';
import { useAsync } from '../lib/useAsync';

function Roster({ classroom }: { classroom: Classroom }) {
  return (
    <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {classroom.students.map((student: Student) => (
        <li key={student.id}>
          <Link
            to={`/students/${student.id}`}
            className="block h-full rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition-colors hover:border-indigo-400 hover:bg-indigo-50"
          >
            <span className="block font-medium text-slate-900">
              {student.name}
            </span>
            <span className="mt-1 block text-sm text-slate-500">
              Grade {student.grade} · {student.pronouns}
            </span>
            <span className="mt-3 block text-sm font-medium text-indigo-700">
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
    return <p className="text-slate-600">You do not teach any classrooms yet.</p>;
  }

  const active = data.find((c) => String(c.id) === activeId) ?? data[0];

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
        Your classrooms
      </h1>
      <p className="mt-2 mb-6 text-slate-600">
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
