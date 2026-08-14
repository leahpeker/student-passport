import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import type { Me } from '../api/types';

const ROLE_LABEL: Record<Me['role'], string> = {
  teacher: 'Teacher',
  guardian: 'Guardian',
  student: 'Student',
};

export function Layout({
  me,
  onSignOut,
  children,
}: {
  me: Me;
  onSignOut: () => void;
  children: ReactNode;
}) {
  return (
    <div className="min-h-screen">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:rounded-md focus:bg-white focus:px-4 focus:py-2 focus:font-medium focus:text-indigo-700 focus:shadow-md"
      >
        Skip to main content
      </a>

      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-4 gap-y-2 px-6 py-4">
          <Link
            to="/"
            className="text-lg font-semibold tracking-tight text-slate-900 hover:text-indigo-700"
          >
            Student Passport
          </Link>
          <p className="ml-auto text-sm text-slate-600">
            <span className="font-medium text-slate-900">
              {me.first_name} {me.last_name}
            </span>
            <span className="mx-2 text-slate-300" aria-hidden="true">
              /
            </span>
            {ROLE_LABEL[me.role]}
          </p>
          <button
            type="button"
            onClick={onSignOut}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:border-slate-400 hover:bg-slate-50"
          >
            Sign out
          </button>
        </div>
      </header>

      <p className="border-b border-amber-200 bg-amber-50 px-6 py-2 text-center text-sm text-amber-900">
        Demonstration build. Every student, record and note shown here is
        synthetic and describes no real person.
      </p>

      <main id="main" className="mx-auto max-w-6xl px-6 py-8">
        {children}
      </main>
    </div>
  );
}
