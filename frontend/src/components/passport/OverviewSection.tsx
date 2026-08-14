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
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
        {VOICES.map((voice) => (
          <article key={voice.key} className="card">
            <h3 className="card-title">{voice.label}</h3>
            <p className="card-body leading-relaxed">
              {sections.overview[voice.key]}
            </p>
          </article>
        ))}
      </div>
    </Section>
  );
}
