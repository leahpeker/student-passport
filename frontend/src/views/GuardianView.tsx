import type { Me } from '../api/types';
import { StudentCards } from '../components/StudentCards';

/**
 * A guardian sees their own children and nothing else. There is deliberately
 * no classroom concept here: `GET /api/classrooms/` returns nothing for a
 * guardian, and `me.students` is the set the server says they may reach.
 */
export function GuardianView({ me }: { me: Me }) {
  if (me.students.length === 0) {
    return (
      <p className="text-muted">No students are linked to this account yet.</p>
    );
  }

  const plural = me.students.length > 1;

  return (
    <div>
      <h1 className="text-[26px] font-medium tracking-[-0.02em] text-text">
        {plural ? 'Your students' : 'Your student'}
      </h1>
      <p className="mt-2 mb-6 text-[13.5px] leading-relaxed text-muted">
        Everything the school records about {plural ? 'your children' : 'your child'},
        in the same view their teachers see — and a place to add what only you
        know.
      </p>

      <StudentCards students={me.students} />
    </div>
  );
}
