import { useState } from 'react';
import type { Me } from '../api/types';
import { PassportPanel } from '../components/passport/PassportPanel';
import { Tabs } from '../components/Tabs';

export function GuardianView({ me }: { me: Me }) {
  const [activeId, setActiveId] = useState<string | null>(null);

  if (me.students.length === 0) {
    return (
      <p className="text-slate-600">
        No students are linked to this account yet.
      </p>
    );
  }

  const active =
    me.students.find((s) => String(s.id) === activeId) ?? me.students[0];

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
        Your students
      </h1>
      <p className="mt-2 mb-6 text-slate-600">
        Everything the school records about your children, in the same view
        their teachers see — and a place to add what only you know.
      </p>

      <Tabs
        label="Your students"
        tabs={me.students.map((student) => ({
          id: String(student.id),
          label: student.name,
          hint: `Grade ${student.grade}`,
        }))}
        activeId={String(active.id)}
        onChange={setActiveId}
      >
        <PassportPanel studentId={active.id} me={me} />
      </Tabs>
    </div>
  );
}
