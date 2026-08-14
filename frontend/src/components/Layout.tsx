import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import type { Me } from '../api/types';
import { useTheme } from '../lib/theme';

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
  const initials = `${me.first_name[0] ?? ''}${me.last_name[0] ?? ''}`.toUpperCase();
  const { theme, toggle } = useTheme();

  return (
    <div className="min-h-screen bg-bg text-text">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:rounded-md focus:bg-surface focus:px-4 focus:py-2 focus:font-medium focus:text-accent focus:shadow-md"
      >
        Skip to main content
      </a>

      <header
        className="flex flex-wrap items-center gap-x-4 gap-y-2 px-7 py-3.5"
        style={{
          background:
            'linear-gradient(180deg, var(--surface-header-start), var(--surface-header-end))',
        }}
      >
        <Link to="/" className="mr-auto flex items-center gap-2.5">
          <span
            aria-hidden="true"
            className="flex h-[22px] w-[22px] items-center justify-center rounded-[6px] border border-accent text-[11px] text-accent"
          >
            P
          </span>
          <span className="text-base font-medium tracking-[-0.01em] text-text">
            Student Passport
          </span>
        </Link>

        <span className="text-[13px] text-muted">{ROLE_LABEL[me.role]}</span>

        <span aria-hidden="true" className="h-5 w-px bg-divider" />

        <span className="text-[13px] text-muted">
          {me.first_name} {me.last_name}
        </span>
        <span
          aria-hidden="true"
          className="avatar h-[26px] w-[26px] text-[11px]"
        >
          {initials}
        </span>

        <button type="button" onClick={toggle} className="btn btn-secondary">
          {theme === 'dark' ? 'Light mode' : 'Dark mode'}
        </button>
        <button type="button" onClick={onSignOut} className="btn btn-secondary">
          Sign out
        </button>
      </header>

      <p className="bg-neutral-900 px-6 py-2 text-center text-sm text-amber-300/90">
        Demonstration build. Every student, record and note shown here is
        synthetic and describes no real person.
      </p>
      <hr className="hr" />

      <main id="main" className="mx-auto max-w-[1440px] px-7 pt-[22.4px] pb-11">
        {children}
      </main>
    </div>
  );
}
