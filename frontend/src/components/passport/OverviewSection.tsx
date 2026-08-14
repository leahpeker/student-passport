import type { PassportSections, Student } from '../../api/types';
import { Section } from '../Section';

const VOICES = [
  { key: 'teacher_voice', label: 'What their teachers see' },
  { key: 'guardian_voice', label: 'What home sees' },
  { key: 'student_voice', label: 'What they say themselves' },
] as const;

export function OverviewSection({
  student,
  sections,
}: {
  student: Student;
  sections: PassportSections;
}) {
  return (
    <Section
      id="overview"
      title="Overview"
      lead={`The same student, described by the three people who know different parts of ${student.first_name}.`}
    >
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {VOICES.map((voice) => (
          <article
            key={voice.key}
            className="rounded-lg border border-slate-200 bg-slate-50/70 p-4"
          >
            <h3 className="text-sm font-semibold tracking-wide text-indigo-800 uppercase">
              {voice.label}
            </h3>
            <p className="mt-3 leading-relaxed text-slate-700">
              {sections.overview[voice.key]}
            </p>
          </article>
        ))}
      </div>
    </Section>
  );
}
