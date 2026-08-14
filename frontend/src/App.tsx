import { useCallback, useEffect, useState } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { getMe, logout } from './api/client';
import type { Me } from './api/types';
import { Layout } from './components/Layout';
import { GuardianView } from './views/GuardianView';
import { LoginView } from './views/LoginView';
import { PassportView } from './views/PassportView';
import { TeacherView } from './views/TeacherView';

/** Sends each role to the view it starts in. */
function Landing({ me }: { me: Me }) {
  if (me.role === 'teacher') return <Navigate to="/teacher" replace />;
  if (me.role === 'guardian') return <Navigate to="/guardian" replace />;
  if (me.student_id != null) return <Navigate to={`/students/${me.student_id}`} replace />;
  return (
    <p className="p-8 text-muted">
      This account is not linked to a student record.
    </p>
  );
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
            <Route path="/teacher" element={<TeacherView />} />
            <Route path="/guardian" element={<GuardianView me={me} />} />
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
