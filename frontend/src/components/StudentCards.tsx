import { Link } from 'react-router-dom';
import type { Student } from '../api/types';
import { AiBadge } from './AiBadge';

function initialsOf(student: Student): string {
  return `${student.first_name[0] ?? ''}${student.last_name[0] ?? ''}`.toUpperCase();
}

/** The roster card grid, shared by the teacher and guardian views. */
export function StudentCards({ students }: { students: Student[] }) {
  return (
    <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {students.map((student) => (
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
              {student.has_ai_analysis && <AiBadge />}
            </div>
            <span className="text-[11px] text-muted">
              Grade {student.grade}
              {student.pronouns ? ` · ${student.pronouns}` : ''}
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
