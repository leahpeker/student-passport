/**
 * Wire types for the Student Passport API.
 *
 * These mirror `passport/models.py`. Keys are the snake_case names the Django
 * API serialises, so a response can be assigned to these types unchanged.
 *
 * All student data in this app is synthetic.
 */

/** `Profile.ROLES`. */
export type Role = 'teacher' | 'guardian' | 'student';

/** `StudentRecord.SOURCES`. */
export type RecordSource =
  | 'sis'
  | 'assessment'
  | 'attendance'
  | 'behavior'
  | 'document'
  | 'ai_tutor'
  | 'engagement'
  | 'observation'
  | 'parent_input'
  | 'student_input'
  | 'question';

export const SOURCE_LABELS: Record<RecordSource, string> = {
  sis: 'Student information system',
  assessment: 'Assessment',
  attendance: 'Attendance',
  behavior: 'Behavior',
  document: 'Document',
  ai_tutor: 'AI tutor interaction',
  engagement: 'Engagement sample',
  observation: 'Teacher observation',
  parent_input: 'Guardian input',
  student_input: 'Student input',
  question: 'Asked question',
};

/** A `User` plus its `Profile.role`, as returned by `GET /api/me/`. */
export interface Me {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  role: Role;
  /** Set when `role === 'student'`: the student this user is. */
  student_id: number | null;
  /** Students this user may view. Their wards, for a guardian. */
  students: Student[];
}

/** `Student`. `name` is the model's `name` property. */
export interface Student {
  id: number;
  first_name: string;
  last_name: string;
  name: string;
  grade: string;
  date_of_birth: string | null;
  /** How the student refers to themselves, e.g. "she/her". */
  pronouns: string;
}

/** `Guardianship`, flattened onto the student it concerns. */
export interface Guardian {
  id: number;
  name: string;
  relationship: string;
}

/** `Classroom`. */
export interface Classroom {
  id: number;
  name: string;
  subject: string;
  /** Blank for mixed-grade classes. */
  grade: string;
  period: string;
  teachers: string[];
  students: Student[];
}

/**
 * `StudentRecord`. `data` is a free JSON bag, populated only where a record
 * carries numbers worth charting. Read it through the narrowing helpers in
 * `records.ts` rather than casting.
 */
export interface StudentRecord {
  id: number;
  student: number;
  source: RecordSource;
  kind: string;
  /** ISO date, `YYYY-MM-DD`. */
  date: string;
  title: string;
  body: string;
  data: Record<string, unknown>;
  /** Display name of the authoring user, or null for system records. */
  author: string | null;
  /** ISO datetime. */
  created_at: string;
}

/**
 * The narrative half of `Passport.sections`. Written by the model from the
 * student's records; the charted sections are derived from the records
 * themselves rather than stored here.
 */
export interface PassportSections {
  overview: {
    teacher_voice: string;
    guardian_voice: string;
    student_voice: string;
  };
  how_they_learn: string;
  performance: string;
  behavior: string;
}

/** `Passport`, plus the student it belongs to and the records behind it. */
export interface Passport {
  student: Student;
  guardians: Guardian[];
  sections: PassportSections;
  /** ISO datetime. */
  generated_at: string;
  record_count: number;
  records: StudentRecord[];
}

/** Result of `POST /api/students/<id>/ask/`. Stored as a `question` record. */
export interface Answer {
  /** The `question` record the exchange was written back as. */
  record: StudentRecord;
  question: string;
  answer: string;
  /** Records the answer drew on, so a reader can check the reasoning. */
  cited_record_ids: number[];
}

/** Body of `POST /api/students/<id>/input/`. */
export interface InputSubmission {
  source: Extract<RecordSource, 'parent_input' | 'student_input'>;
  title: string;
  body: string;
}

/** The one-day computed triage behind a `Digest`. Never invented by the model. */
export interface DigestFlag {
  topic: string;
  kind: 'accuracy' | 'pace';
  severity: 'concern' | 'watch';
  detail: string;
}

export interface DigestTopic {
  topic: string;
  attempted: number;
  correct: number;
  accuracy: number;
  avg_seconds: number;
}

export type DigestAction = 'intervene' | 'check_in' | 'celebrate';

/**
 * `GET /api/students/<id>/digest/` — one day's AI-tutor/practice-session
 * activity, triaged deterministically from `flags` (`action` is never left to
 * the model). `date`/`generated_at` are null and `narrative` is empty when the
 * student has no app-integration activity on file at all. `insights` is only
 * present once a day has been narrated, so treat it as optional.
 */
export interface Digest {
  student_id: number;
  date: string | null;
  generated_at: string | null;
  record_count: number;
  action: DigestAction;
  headline: string;
  narrative: string;
  topics: DigestTopic[];
  flags: DigestFlag[];
  insights?: string[];
}
