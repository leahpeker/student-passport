import { Navigate, useParams } from 'react-router-dom';
import type { Me } from '../api/types';
import { PassportPanel } from '../components/passport/PassportPanel';
import { StudentSidebar } from '../components/passport/StudentSidebar';
import { canViewStudent, landingPath } from '../lib/access';

export function PassportView({ me }: { me: Me }) {
  const { studentId } = useParams();
  const id = Number(studentId);

  // A link from an older session can point at an id this user cannot reach.
  // Send them to their own view instead of surfacing the API's 404.
  if (!Number.isInteger(id) || !canViewStudent(me, id)) {
    return <Navigate to={landingPath(me)} replace />;
  }

  return (
    <div className="grid gap-5 lg:grid-cols-[236px_1fr]">
      <StudentSidebar me={me} activeStudentId={id} />
      <PassportPanel studentId={id} me={me} />
    </div>
  );
}
