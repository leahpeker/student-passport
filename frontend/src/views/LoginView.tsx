import { useState } from 'react';
import { DEMO_LOGINS, DEMO_PASSWORD, login } from '../api/client';
import type { Me } from '../api/types';

export function LoginView({ onSignedIn }: { onSignedIn: (me: Me) => void }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      onSignedIn(await login(username, password));
    } catch {
      setError('That username and password do not match a demo account.');
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-lg flex-col justify-center bg-bg px-6 py-12 text-text">
      <div className="flex items-center gap-2.5">
        <span
          aria-hidden="true"
          className="flex h-[22px] w-[22px] items-center justify-center rounded-[6px] border border-accent text-[11px] text-accent"
        >
          P
        </span>
        <h1 className="text-[26px] font-medium tracking-[-0.02em] text-text">
          Student Passport
        </h1>
      </div>
      <p className="mt-3 text-[13.5px] leading-relaxed text-muted">
        One portable view of a student, gathered from every source that already
        describes them — and handed to whoever needs it next.
      </p>

      <form onSubmit={onSubmit} className="card elev-sm mt-8 gap-4 p-[19px]">
        <h2 className="text-[17px] font-medium tracking-[-0.015em] text-text">
          Sign in
        </h2>

        <div className="field">
          <label htmlFor="username">Username</label>
          <input
            id="username"
            name="username"
            type="text"
            autoComplete="username"
            required
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="input"
          />
        </div>

        <div className="field">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input"
          />
        </div>

        {error && (
          <p role="alert" className="rounded-md bg-red-950/40 px-3 py-2 text-[13px] text-red-300">
            {error}
          </p>
        )}

        <button type="submit" disabled={pending} className="btn btn-primary w-full">
          {pending ? 'Signing in…' : 'Sign in'}
        </button>
      </form>

      <section aria-labelledby="demo-accounts" className="card elev-sm mt-6 p-[19px]">
        <h2 id="demo-accounts" className="card-title">
          Demo accounts
        </h2>
        <p className="text-[13px] text-muted">
          All use the password <code className="font-mono">{DEMO_PASSWORD}</code>.
          Every account and every student behind it is synthetic.
        </p>
        <ul className="mt-2 space-y-2">
          {DEMO_LOGINS.map((account) => (
            <li key={account.username}>
              <button
                type="button"
                onClick={() => {
                  setUsername(account.username);
                  setPassword(DEMO_PASSWORD);
                }}
                className="flex w-full items-baseline gap-3 rounded-md bg-[var(--surface-well)] px-3 py-2 text-left text-[13px] hover:opacity-80"
              >
                <span className="font-mono font-medium text-text">
                  {account.username}
                </span>
                <span className="text-muted">{account.note}</span>
                <span className="ml-auto text-[11px] font-medium text-accent">
                  Use
                </span>
              </button>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
