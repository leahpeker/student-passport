import { useCallback, useState } from 'react';
import { getClassrooms } from '../api/client';
import { AsyncState } from '../components/AsyncState';
import { Tabs } from '../components/Tabs';
import { TeacherRoster } from '../components/TeacherRoster';
import { useAsync } from '../lib/useAsync';

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
        <TeacherRoster classroom={active} />
      </Tabs>
    </div>
  );
}
