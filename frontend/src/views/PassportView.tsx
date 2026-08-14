import { Link, useParams } from 'react-router-dom';
import type { Me } from '../api/types';
import { PassportPanel } from '../components/passport/PassportPanel';

export function PassportView({ me }: { me: Me }) {
  const { studentId } = useParams();
  const id = Number(studentId);

  if (!Number.isInteger(id)) {
    return <p className="text-muted">That is not a student we can show.</p>;
  }

  return (
    <div>
      {me.role === 'teacher' && (
        <p className="mb-4">
          <Link to="/teacher" className="btn btn-ghost -ml-2">
            ← Back to your classrooms
          </Link>
        </p>
      )}
      <PassportPanel studentId={id} me={me} />
    </div>
  );
}
