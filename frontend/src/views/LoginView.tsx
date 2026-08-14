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
    <main className="mx-auto flex min-h-screen max-w-lg flex-col justify-center px-6 py-12">
      <h1 className="text-3xl font-semibold tracking-tight text-slate-900">
        Student Passport
      </h1>
      <p className="mt-3 leading-relaxed text-slate-600">
        One portable view of a student, gathered from every source that already
        describes them — and handed to whoever needs it next.
      </p>

      <form
        onSubmit={onSubmit}
        className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
      >
        <h2 className="text-lg font-semibold tracking-tight text-slate-900">
          Sign in
        </h2>

        <div className="mt-5">
          <label
            htmlFor="username"
            className="block text-sm font-medium text-slate-700"
          >
            Username
          </label>
          <input
            id="username"
            name="username"
            type="text"
            autoComplete="username"
            required
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-slate-900 placeholder:text-slate-400 focus:border-indigo-600"
          />
        </div>

        <div className="mt-4">
          <label
            htmlFor="password"
            className="block text-sm font-medium text-slate-700"
          >
            Password
          </label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-slate-900 focus:border-indigo-600"
          />
        </div>

        {error && (
          <p
            role="alert"
            className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800"
          >
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={pending}
          className="mt-6 w-full rounded-md bg-indigo-700 px-4 py-2.5 font-medium text-white hover:bg-indigo-800 disabled:opacity-60"
        >
          {pending ? 'Signing in…' : 'Sign in'}
        </button>
      </form>

      <section
        aria-labelledby="demo-accounts"
        className="mt-6 rounded-xl border border-slate-200 bg-white p-6"
      >
        <h2
          id="demo-accounts"
          className="text-sm font-semibold tracking-tight text-slate-900"
        >
          Demo accounts
        </h2>
        <p className="mt-1 text-sm text-slate-600">
          All use the password <code className="font-mono">{DEMO_PASSWORD}</code>.
          Every account and every student behind it is synthetic.
        </p>
        <ul className="mt-4 space-y-2">
          {DEMO_LOGINS.map((account) => (
            <li key={account.username}>
              <button
                type="button"
                onClick={() => {
                  setUsername(account.username);
                  setPassword(DEMO_PASSWORD);
                }}
                className="flex w-full items-baseline gap-3 rounded-md border border-slate-200 px-3 py-2 text-left text-sm hover:border-indigo-300 hover:bg-indigo-50"
              >
                <span className="font-mono font-medium text-slate-900">
                  {account.username}
                </span>
                <span className="text-slate-500">{account.note}</span>
                <span className="ml-auto text-xs font-medium text-indigo-700">
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
