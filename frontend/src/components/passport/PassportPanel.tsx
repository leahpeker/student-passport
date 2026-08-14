import { useCallback, useState } from 'react';
import { exportPassport, getPassport } from '../../api/client';
import type { Me, Passport, StudentRecord } from '../../api/types';
import { useAsync } from '../../lib/useAsync';
import { formatDate } from '../../lib/school';
import { AsyncState } from '../AsyncState';
import { BehaviorSection } from './BehaviorSection';
import { HowTheyLearnSection } from './HowTheyLearnSection';
import { InputSection } from './InputSection';
import { OverviewSection } from './OverviewSection';
import { PerformanceSection } from './PerformanceSection';
import { QuestionBox } from './QuestionBox';

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-[10.5px] font-medium tracking-[0.08em] text-muted uppercase">
        {label}
      </dt>
      <dd className="mt-1 text-[13px] text-text">{value}</dd>
    </div>
  );
}

export function PassportPanel({ studentId, me }: { studentId: number; me: Me }) {
  const load = useCallback(() => getPassport(studentId), [studentId]);
  const { data, error, loading, setData } = useAsync(load);
  const [exportError, setExportError] = useState<string | null>(null);

  const addRecord = useCallback(
    (record: StudentRecord) => {
      setData((current: Passport | null) =>
        current ? { ...current, records: [record, ...current.records] } : current,
      );
    },
    [setData],
  );

  async function onExport() {
    setExportError(null);
    try {
      const bundle = await exportPassport(studentId);
      const url = URL.createObjectURL(
        new Blob([JSON.stringify(bundle, null, 2)], { type: 'application/json' }),
      );
      const link = document.createElement('a');
      link.href = url;
      link.download = `student-passport-${studentId}.json`;
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      setExportError('The export could not be produced.');
    }
  }

  if (loading || error) {
    return <AsyncState loading={loading} error={error} label="this passport" />;
  }
  if (!data) return null;

  const { student, sections, records, guardians } = data;
  const sourceCount = new Set(records.map((r) => r.source)).size;

  const initials = `${student.first_name[0] ?? ''}${student.last_name[0] ?? ''}`.toUpperCase();

  return (
    <article className="space-y-6">
      <header className="elev-sm rounded-lg bg-surface p-[19px]">
        <div className="flex flex-wrap items-start gap-4">
          <span aria-hidden="true" className="avatar h-[54px] w-[54px] text-[19px]">
            {initials}
          </span>
          <div>
            <h1 className="text-[26px] font-medium tracking-[-0.02em] text-text">
              {student.name}
            </h1>
            <p className="mt-1 text-[12.5px] text-muted">
              Grade {student.grade} · {student.pronouns}
            </p>
          </div>
          <button type="button" onClick={onExport} className="btn btn-secondary ml-auto">
            Export as JSON
          </button>
        </div>
        {exportError && (
          <p role="alert" className="mt-3 text-[13px] text-red-300">
            {exportError}
          </p>
        )}
        <hr className="hr mt-5" />
        <dl className="mt-5 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <Stat label="Records" value={String(records.length)} />
          <Stat label="Sources" value={String(sourceCount)} />
          <Stat
            label="Guardians"
            value={guardians.map((g) => g.name).join(', ') || 'None on file'}
          />
          <Stat
            label="Assembled"
            value={formatDate(data.generated_at.slice(0, 10))}
          />
        </dl>
      </header>

      <OverviewSection student={student} sections={sections} />
      <HowTheyLearnSection records={records} narrative={sections.how_they_learn} />
      <PerformanceSection records={records} narrative={sections.performance} />
      <BehaviorSection records={records} narrative={sections.behavior} />

      <InputSection
        id="guardian-input"
        title="Guardian input"
        lead="What the people at home have asked the school to know. Nothing here comes from a system; it was written by a guardian."
        source="parent_input"
        studentId={studentId}
        records={records.filter((r) => r.source === 'parent_input')}
        canWrite={me.role === 'guardian'}
        formLabel="Add a note from home"
        onAdded={addRecord}
      />

      <InputSection
        id="student-input"
        title="Student input"
        lead={`What ${student.first_name} has asked to be passed on. This is the only section the student writes.`}
        source="student_input"
        studentId={studentId}
        records={records.filter((r) => r.source === 'student_input')}
        canWrite={me.role === 'student' && me.student_id === studentId}
        formLabel="Add something in your own words"
        onAdded={addRecord}
      />

      <QuestionBox
        student={student}
        onAnswered={(answer) => addRecord(answer.record)}
      />
    </article>
  );
}
