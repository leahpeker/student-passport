import { useCallback, useMemo, useRef, useState } from 'react';
import { exportPassport, getDigest, getPassport } from '../../api/client';
import type { Me, Passport, StudentRecord } from '../../api/types';
import { useAsync } from '../../lib/useAsync';
import { formatDate } from '../../lib/school';
import { getPulse, pulseFromDigest } from '../../lib/pulse';
import { showsBehavior } from '../../lib/access';
import { AsyncState } from '../AsyncState';
import { Tabs, type TabItem } from '../Tabs';
import { BehaviorSection } from './BehaviorSection';
import { HowTheyLearnSection } from './HowTheyLearnSection';
import { InputSection } from './InputSection';
import { OverviewSection } from './OverviewSection';
import { PerformanceSection } from './PerformanceSection';
import { PassportAssistant, type AssistantHandle } from './PassportAssistant';
import { PulseHero } from './PulseHero';

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
  // Teacher-only on the backend and null for anyone else — see getDigest.
  // Falls back to the authored fixture below rather than showing an error.
  const loadDigest = useCallback(() => getDigest(studentId), [studentId]);
  const { data: digest } = useAsync(loadDigest);
  const [exportError, setExportError] = useState<string | null>(null);
  const [tab, setTab] = useState('overview');
  const assistantRef = useRef<AssistantHandle>(null);
  const ask = useCallback((prompt?: string) => assistantRef.current?.ask(prompt), []);

  const addRecord = useCallback(
    (record: StudentRecord) => {
      setData((current: Passport | null) =>
        current ? { ...current, records: [record, ...current.records] } : current,
      );
    },
    [setData],
  );

  const tabs = useMemo<TabItem[]>(() => {
    const list: TabItem[] = [
      { id: 'overview', label: 'Overview' },
      { id: 'learning', label: 'Learning' },
      { id: 'performance', label: 'Performance over time' },
    ];
    if (showsBehavior(me.role)) list.push({ id: 'behavior', label: 'Behaviour' });
    return list;
  }, [me.role]);

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
  const pulse = digest ? pulseFromDigest(digest, student.first_name) : getPulse(studentId);
  const sourceCount = new Set(records.map((r) => r.source)).size;
  const initials = `${student.first_name[0] ?? ''}${student.last_name[0] ?? ''}`.toUpperCase();

  const active = tabs.some((t) => t.id === tab) ? tab : 'overview';

  return (
    <article>
      {/* top row: student info (~1/3) + pulse hero (~2/3) */}
      <div className="grid gap-4 lg:grid-cols-[1fr_2fr]">
        <header className="rounded-lg bg-surface p-[19px] elev-sm">
          <div className="flex items-start gap-3">
            <span aria-hidden="true" className="avatar h-[46px] w-[46px] text-[17px]">
              {initials}
            </span>
            <div className="min-w-0">
              <h1 className="truncate text-[21px] font-medium tracking-[-0.02em] text-text">
                {student.name}
              </h1>
              <p className="mt-0.5 text-[12px] text-muted">
                Grade {student.grade} · {student.pronouns}
              </p>
            </div>
          </div>
          <hr className="hr mt-4" />
          <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-3">
            <Stat label="Records" value={String(records.length)} />
            <Stat label="Sources" value={String(sourceCount)} />
            <Stat
              label="Guardians"
              value={guardians.map((g) => g.name).join(', ') || 'None on file'}
            />
            <Stat label="Assembled" value={formatDate(data.generated_at.slice(0, 10))} />
          </dl>
          <button type="button" onClick={onExport} className="btn btn-secondary mt-4 w-full">
            Export as JSON
          </button>
          {exportError && (
            <p role="alert" className="mt-2 text-[12.5px] text-red-300">
              {exportError}
            </p>
          )}
        </header>

        <PulseHero student={student} pulse={pulse} onAsk={ask} />
      </div>

      {/* category nav */}
      <div className="mt-6">
        <Tabs label="Passport sections" tabs={tabs} activeId={active} onChange={setTab}>
          {active === 'overview' && (
            <div className="space-y-6">
              <OverviewSection student={student} sections={sections} />
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
            </div>
          )}
          {active === 'learning' && (
            <HowTheyLearnSection records={records} narrative={sections.how_they_learn} />
          )}
          {active === 'performance' && (
            <PerformanceSection records={records} narrative={sections.performance} />
          )}
          {active === 'behavior' && (
            <BehaviorSection records={records} narrative={sections.behavior} />
          )}
        </Tabs>
      </div>

      <PassportAssistant
        ref={assistantRef}
        student={student}
        pulse={pulse}
        onAnswered={(answer) => addRecord(answer.record)}
      />
    </article>
  );
}
