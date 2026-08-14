import { useCallback, useEffect, useState, type ReactElement } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { getMe, logout } from './api/client';
import type { Me, Role } from './api/types';
import { Layout } from './components/Layout';
import { landingPath } from './lib/access';
import { GuardianView } from './views/GuardianView';
import { LoginView } from './views/LoginView';
import { PassportView } from './views/PassportView';
import { TeacherView } from './views/TeacherView';

/** Sends each role to the view it starts in. */
function Landing({ me }: { me: Me }) {
  if (me.role === 'student' && me.student_id == null) {
    return (
      <p className="p-8 text-muted">
        This account is not linked to a student record.
      </p>
    );
  }
  return <Navigate to={landingPath(me)} replace />;
}

/**
 * Keeps one role out of another's view. A guardian who lands on /teacher is
 * sent to their own students rather than told they teach nothing.
 */
function RequireRole({
  me,
  role,
  children,
}: {
  me: Me;
  role: Role;
  children: ReactElement;
}) {
  if (me.role !== role) return <Navigate to={landingPath(me)} replace />;
  return children;
}

export default function App() {
  const [me, setMe] = useState<Me | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    let cancelled = false;
    getMe()
      .then((session) => {
        if (!cancelled) setMe(session);
      })
      .catch(() => {
        if (!cancelled) setMe(null);
      })
      .finally(() => {
        if (!cancelled) setChecking(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const signOut = useCallback(async () => {
    await logout();
    setMe(null);
  }, []);

  if (checking) {
    return (
      <p role="status" className="min-h-screen bg-bg p-8 text-muted">
        Loading…
      </p>
    );
  }

  return (
    <BrowserRouter>
      {me ? (
        <Layout me={me} onSignOut={signOut}>
          <Routes>
            <Route path="/" element={<Landing me={me} />} />
            <Route
              path="/teacher"
              element={
                <RequireRole me={me} role="teacher">
                  <TeacherView />
                </RequireRole>
              }
            />
            <Route
              path="/guardian"
              element={
                <RequireRole me={me} role="guardian">
                  <GuardianView me={me} />
                </RequireRole>
              }
            />
            <Route path="/students/:studentId" element={<PassportView me={me} />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Layout>
      ) : (
        <Routes>
          <Route path="*" element={<LoginView onSignedIn={setMe} />} />
        </Routes>
      )}
    </BrowserRouter>
  );
}
