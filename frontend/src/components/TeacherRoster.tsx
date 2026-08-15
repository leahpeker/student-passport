import { Link } from 'react-router-dom';
import type { Classroom, Student } from '../api/types';
import { useClassroomPulses } from '../lib/useRosterPulse';
import type { Pulse, PulseTone } from '../lib/pulse';
import { toneCard, toneDot, toneLabel } from './passport/tone';

function initialsOf(student: Student): string {
  return `${student.first_name[0] ?? ''}${student.last_name[0] ?? ''}`.toUpperCase();
}

/** Worst-first, so a teacher sees who needs attention before who is fine. */
const TONE_ORDER: PulseTone[] = ['red', 'amber', 'green'];

function StudentCard({ student, pulse }: { student: Student; pulse: Pulse }) {
  return (
    <li>
      <Link
        to={`/students/${student.id}`}
        className="card elev-sm block h-full transition-colors hover:bg-neutral-800/40"
      >
        <div className="flex items-center gap-2.5">
          <span aria-hidden="true" className="avatar h-7 w-7 shrink-0 text-[11px]">
            {initialsOf(student)}
          </span>
          <span className="truncate text-[13.5px] font-medium text-text">
            {student.name}
          </span>
          <span
            aria-hidden="true"
            className={`ml-auto h-2 w-2 shrink-0 rounded-full ${toneDot[pulse.tone]}`}
          />
        </div>
        <span className="text-[11px] text-muted">
          Grade {student.grade}
          {student.pronouns ? ` · ${student.pronouns}` : ''}
        </span>
        <span className="mt-1 line-clamp-1 text-[12px] text-muted">{pulse.trendNote}</span>
        <span className="mt-1 text-[12px] font-medium text-accent">Open passport</span>
      </Link>
    </li>
  );
}

function ToneSection({
  tone,
  students,
  pulses,
}: {
  tone: PulseTone;
  students: Student[];
  pulses: Record<number, Pulse>;
}) {
  if (students.length === 0) return null;
  return (
    <section className={`mb-6 rounded-lg border p-3 ${toneCard[tone]}`}>
      <h3 className="mb-3 flex items-center gap-2 text-[12px] font-medium tracking-[0.04em] text-text uppercase">
        <span aria-hidden="true" className={`h-2 w-2 rounded-full ${toneDot[tone]}`} />
        {toneLabel[tone]}
        <span className="text-muted normal-case">({students.length})</span>
      </h3>
      <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {students.map((student) => (
          <StudentCard key={student.id} student={student} pulse={pulses[student.id]} />
        ))}
      </ul>
    </section>
  );
}

/** A classroom's roster, grouped into Needs attention / Watch / On track
 * sections by each student's pulse — worst first, so it reads as a triage
 * list rather than an alphabetical grid. */
export function TeacherRoster({ classroom }: { classroom: Classroom }) {
  const pulses = useClassroomPulses(classroom.students);
  const byTone: Record<PulseTone, Student[]> = { red: [], amber: [], green: [] };
  for (const student of classroom.students) {
    byTone[pulses[student.id]?.tone ?? 'green'].push(student);
  }

  return (
    <div>
      {TONE_ORDER.map((tone) => (
        <ToneSection key={tone} tone={tone} students={byTone[tone]} pulses={pulses} />
      ))}
    </div>
  );
}
