import { Link, Navigate, useParams } from 'react-router-dom';
import type { Me } from '../api/types';
import { PassportPanel } from '../components/passport/PassportPanel';
import { canViewStudent, landingPath } from '../lib/access';

export function PassportView({ me }: { me: Me }) {
  const { studentId } = useParams();
  const id = Number(studentId);

  // A link from an older session can point at an id this user cannot reach.
  // Send them to their own view instead of surfacing the API's 404.
  if (!Number.isInteger(id) || !canViewStudent(me, id)) {
    return <Navigate to={landingPath(me)} replace />;
  }

  const backTo = me.role === 'teacher' ? '/teacher' : '/guardian';
  const backLabel =
    me.role === 'teacher' ? '← Back to your classrooms' : '← Back to your students';

  return (
    <div>
      {me.role !== 'student' && (
        <p className="mb-4">
          <Link to={backTo} className="btn btn-ghost -ml-2">
            {backLabel}
          </Link>
        </p>
      )}
      <PassportPanel studentId={id} me={me} />
    </div>
  );
}
