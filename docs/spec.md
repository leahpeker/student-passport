# Student Passport — design

Hackathon build. All data is synthetic.

## Problem

A student's information is scattered across systems, and the most useful signals
— what a teacher noticed, what the student asks an AI tutor, when they are
engaged — are usually never recorded. When a student changes teacher or school,
the next adult starts over. The passport gathers those sources into one view
that travels with the student and can be handed to a person or another tool.

## Stack

| Layer | Choice |
| --- | --- |
| Backend | Django 6 + Django REST Framework, Postgres |
| Auth | Django session auth, seeded users |
| Frontend | React + Vite + TypeScript + Tailwind, Recharts |
| LLM | Claude `anthropic.claude-opus-5` on Amazon Bedrock |
| Hosting | Railway (web + Postgres), single service |

Bedrock auth is a Bedrock API key in `AWS_BEARER_TOKEN_BEDROCK`, which the SDK
sends as a bearer token. It cannot be combined with AWS profile credentials —
the key replaces them.
| Speech | Browser-native Web Speech API |

## Data model

```
User ─1:1─ Profile(role: teacher | guardian | student)
Student(user, first_name, last_name, grade, date_of_birth)
Guardianship(guardian, student, relationship)     # M2M
Classroom(name, subject, grade?, period) ─M2M─ teachers, students
StudentRecord(student, source, kind, date, title, body, data?, author?)
Passport(student, sections:JSON, generated_at, record_count)
```

`StudentRecord` holds every source in one table rather than one table per
source. Sources: `sis`, `assessment`, `attendance`, `behavior`, `document`,
`ai_tutor`, `observation`, `parent_input`, `student_input`, `question`. The
payoff is that the passport is a filter over one table and the "hand this to
another tool" story is a single export endpoint rather than a schema
negotiation.

Records are free text first: `body` carries the note, the observation, the
document text. `data` is an optional JSON bag used only where a record has
numbers worth charting — a score, an attendance count, an engagement rating.
A teacher observation is body-only and leaves `data` empty.

`Guardianship` is many-to-many rather than one guardian per student, so two
parents is representable.

## Permissions

One `can_view_student(user, student)` helper, called by every student-scoped
endpoint:

- Teacher — students in classrooms they teach
- Guardian — students they have a `Guardianship` for
- Student — themselves

Anything else returns 404, not 403, so the endpoint does not confirm the student
exists.

## Endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /api/me/` | Current user and role |
| `GET /api/classrooms/` | Classrooms visible to the caller |
| `GET /api/students/<id>/passport/` | Cached narrative; `?refresh=1` regenerates |
| `GET /api/students/<id>/records/` | Raw records, filterable by source |
| `POST /api/students/<id>/ask/` | Question → Claude → answer, stored as a record |
| `POST /api/students/<id>/input/` | Guardian or student contribution |
| `GET /api/students/<id>/export/` | Full passport as JSON, for handoff |

`ask/` builds context from the student's records plus the cached passport, calls
Claude, and writes the exchange back as a `question` record — so asking
questions adds to the passport rather than just reading it.

## Passport sections

Overview (teacher / guardian / student voices), how they learn, performance over
time, behavior over time, guardian input, student input, question box.

## Seed data

Generated from authored story arcs rather than random values. Each arc emits
correlated records across every source, so a real signal exists to find — a
Monday attendance dip, pre-lunch behavior flags, strong afternoon engagement,
and a guardian note about a night shift should resolve to the same underlying
cause. Around six arcs plus lighter generated students to fill class rosters.

## Phases

1. Repo, Django scaffold, models, admin, README, license ✅
2. Seed generator from story arcs
3. API endpoints, permissions, Bedrock integration
4. React shell, auth, role-based routing
5. Passport UI, charts, question box, microphone

## Deliberate simplifications

- SQLite, single process. Fine for a demo; no concurrent-write story.
- Passport narrative is cached on a single row per student and regenerated on
  demand. No background job, no partial invalidation.
- No pagination on record endpoints. Record counts per student are small here.
