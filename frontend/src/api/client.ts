/**
 * The only place the app gets data.
 *
 * Components must import from this module and nowhere else — never from
 * `mock.ts` directly. Every function is already shaped like the endpoint that
 * will back it, so moving from fixtures to the real API is a change here and
 * nowhere else.
 *
 * ## Swapping the fixtures for the API
 *
 * 1. Set `VITE_USE_MOCKS=false`. Every function below then takes its `fetch`
 *    branch instead of its fixture branch. No component changes.
 * 2. `login` becomes a real POST; the browser stores the Django session
 *    cookie. `credentials: 'include'` is already set on every request.
 *
 * In development the API is on a different origin (Django on :8000, Vite on
 * :5173), so requests are cross-origin and Django needs CORS plus
 * `SESSION_COOKIE_SAMESITE`. In production both are served from one origin and
 * `API_BASE_URL` is empty, so the same code makes same-origin requests.
 */

import type {
  Answer,
  Classroom,
  InputSubmission,
  Me,
  Passport,
  RecordSource,
  StudentRecord,
} from './types';
import * as mock from './mock';

/** The one place the dev/production origin difference lives. */
export const API_BASE_URL = import.meta.env.DEV ? 'http://localhost:8000' : '';

/** Fixtures are on unless explicitly turned off. */
const USE_MOCKS = import.meta.env.VITE_USE_MOCKS !== 'false';

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

/** Keeps the demo from painting a loaded state before the browser has drawn. */
function settle<T>(value: T): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), 180));
}

async function fetchJson<T>(path: string, init: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!response.ok) {
    throw new ApiError(`${init.method ?? 'GET'} ${path} failed`, response.status);
  }
  return (await response.json()) as T;
}

function request<T>(path: string, init: RequestInit, fixture: () => T): Promise<T> {
  return USE_MOCKS ? settle(fixture()) : fetchJson<T>(path, init);
}

// ---------------------------------------------------------------------------
// Session
// ---------------------------------------------------------------------------

const SESSION_KEY = 'student-passport.session';

/**
 * Who is signed in. With fixtures this is the browser's own storage; against
 * the real API the session lives in a Django cookie and `getMe` is the source
 * of truth, so this cache is only ever a starting guess.
 */
function cacheSession(me: Me | null): void {
  if (me) sessionStorage.setItem(SESSION_KEY, JSON.stringify(me));
  else sessionStorage.removeItem(SESSION_KEY);
}

function cachedSession(): Me | null {
  const raw = sessionStorage.getItem(SESSION_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Me;
  } catch {
    return null;
  }
}

function requireSession(): Me {
  const me = cachedSession();
  if (!me) throw new ApiError('Not signed in', 403);
  return me;
}

/**
 * `POST /api/login/`. With fixtures this checks the demo account table.
 * Against Django it posts the credentials and the session cookie comes back
 * on the response.
 */
export async function login(username: string, password: string): Promise<Me> {
  const me = await request<Me>(
    '/api/login/',
    { method: 'POST', body: JSON.stringify({ username, password }) },
    () => {
      const found = mock.authenticate(username, password);
      if (!found) throw new ApiError('That username and password do not match.', 401);
      return found;
    },
  );
  cacheSession(me);
  return me;
}

/** `POST /api/logout/`. */
export async function logout(): Promise<void> {
  await request<unknown>('/api/logout/', { method: 'POST' }, () => null);
  cacheSession(null);
}

/** `GET /api/me/`. Resolves to null when nobody is signed in. */
export async function getMe(): Promise<Me | null> {
  try {
    const me = await request<Me>('/api/me/', {}, requireSession);
    cacheSession(me);
    return me;
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      cacheSession(null);
      return null;
    }
    throw error;
  }
}

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

/** `GET /api/classrooms/` — classrooms visible to the caller. */
export function getClassrooms(): Promise<Classroom[]> {
  return request('/api/classrooms/', {}, () => mock.classroomsFor(requireSession()));
}

/**
 * `GET /api/students/<id>/passport/` — the narrative plus the records behind
 * it. Against the real API this is two requests joined here, so the passport
 * page still makes one call.
 */
export async function getPassport(studentId: number): Promise<Passport> {
  if (!USE_MOCKS) {
    const [passport, records] = await Promise.all([
      fetchJson<Omit<Passport, 'records'>>(`/api/students/${studentId}/passport/`, {}),
      getRecords(studentId),
    ]);
    return { ...passport, records };
  }
  return request(`/api/students/${studentId}/passport/`, {}, () => {
    const passport = mock.passportFor(studentId);
    if (!passport) throw new ApiError('No passport for that student.', 404);
    return passport;
  });
}

/** `GET /api/students/<id>/records/`, optionally filtered by source. */
export function getRecords(
  studentId: number,
  source?: RecordSource,
): Promise<StudentRecord[]> {
  const query = source ? `?source=${source}` : '';
  return request(`/api/students/${studentId}/records/${query}`, {}, () => {
    const records = mock.recordsFor(studentId);
    return source ? records.filter((r) => r.source === source) : records;
  });
}

/**
 * `POST /api/students/<id>/ask/` — question to Claude, answered from the
 * student's records and written back as a `question` record.
 */
export function askQuestion(studentId: number, question: string): Promise<Answer> {
  return request(
    `/api/students/${studentId}/ask/`,
    { method: 'POST', body: JSON.stringify({ question }) },
    () => mock.answerFor(studentId, question),
  );
}

/** `POST /api/students/<id>/input/` — a guardian or student contribution. */
export function submitInput(
  studentId: number,
  submission: InputSubmission,
): Promise<StudentRecord> {
  return request(
    `/api/students/${studentId}/input/`,
    { method: 'POST', body: JSON.stringify(submission) },
    () =>
      mock.addRecord(studentId, {
        source: submission.source,
        kind: submission.source === 'parent_input' ? 'guardian note' : 'student note',
        date: new Date().toISOString().slice(0, 10),
        title: submission.title,
        body: submission.body,
        data: {},
        author: `${requireSession().first_name} ${requireSession().last_name}`,
      }),
  );
}

/** `GET /api/students/<id>/export/` — the whole passport, for handing on. */
export function exportPassport(studentId: number): Promise<Passport> {
  return request(`/api/students/${studentId}/export/`, {}, () => {
    const passport = mock.passportFor(studentId);
    if (!passport) throw new ApiError('No passport for that student.', 404);
    return passport;
  });
}

/** Demo credentials shown on the login form. Drops out with the fixtures. */
export const DEMO_LOGINS = mock.DEMO_LOGINS;
export const DEMO_PASSWORD = mock.DEMO_PASSWORD;
