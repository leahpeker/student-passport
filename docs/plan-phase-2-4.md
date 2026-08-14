# Plan — seed generator and frontend shell

Two independent workstreams for the student-passport hackathon build. See
`docs/spec.md` for the overall design.

## Global Constraints

- All student data is synthetic. Never imply otherwise in code, comments, UI
  copy, or generated text.
- Python 3.13, Django 6.1, DRF. Run `.venv/bin/python manage.py check` before
  reporting done. There is no linter or type-checker configured for Python.
- Frontend is TypeScript with `strict` on. Run `npx tsc --noEmit` and
  `npm run build` before reporting done. Fix all errors.
- Do not run any `git` command. The controller owns all commits. Just leave
  your files on disk.
- Task 1 touches only `passport/` (excluding `passport/migrations/`). Task 2
  touches only `frontend/`. Never edit outside your task's directory.
- Do not modify `passport/models.py` — the schema is fixed. Read it to learn
  the field names.
- Use they/them for any student whose pronouns are not explicitly given in
  this plan.

## Task 1 — Story-arc seed generator

Build a deterministic, idempotent seed generator that populates the demo
database with synthetic students whose records tell a coherent story.

**The point of this task:** a demo insight is only impressive if a real signal
exists to find. Random values produce noise no insight can be drawn from.
Every arc must emit *correlated* records across multiple sources, so that the
underlying cause is genuinely inferable from the data without ever being
stated outright in any single record.

### Files to create

- `passport/seed/__init__.py`
- `passport/seed/arcs.py` — the authored arcs, data only
- `passport/seed/generate.py` — turns arcs into database rows
- `passport/management/commands/seed_demo.py` — the command

### Requirements

1. `python manage.py seed_demo` populates the database. `--reset` deletes
   previously seeded data first. Running it twice without `--reset` must not
   duplicate rows.
2. Deterministic: use `random.Random(seed)` with a fixed per-student seed so
   repeated runs produce identical data. Never use the global `random` module.
3. School year runs 2025-09-02 to 2026-06-05. All dates fall inside it, on
   weekdays.
4. Create, at minimum:
   - 6 "hero" students, one per arc below, with rich correlated records
   - ~24 filler students with lighter records, so class rosters look real
   - 4 teachers, each teaching 2-3 classrooms
   - 1-2 guardians per student, some guardians with two students
   - 6-8 classrooms across subjects, students enrolled in 4-6 each
5. Every user gets a `Profile` with the right role. Every student gets a
   `User` (the schema requires it). Seeded password is `demo12345` for all
   accounts; print the login table at the end of the command.
6. Records per hero student should span every source in
   `StudentRecord.SOURCES` except `question` (that source is written at
   runtime when someone asks a question).
7. `data` is a JSON bag used *only* where a record has numbers worth
   charting — assessment scores, attendance counts, engagement ratings.
   Free-text records (observations, guardian input, documents) put their
   content in `body` and leave `data` empty. Do not invent a JSON schema for
   prose.
8. Engagement records: sample several periods per week across the year, with
   `data` carrying at least `{"period": int, "rating": 1-5}`. This is what
   drives the "when is this student most engaged" view, so the per-arc shape
   of this curve matters.

### The six arcs

Each needs correlated evidence across sources. The "underlying truth" must be
*inferable* but never stated outright in a record.

1. **Maya Okonkwo** (she/her), grade 10 — high achiever masking anxiety.
   Top scores that stay top; engagement declining through the year; AI tutor
   questions timestamped 11pm-2am, increasingly about whether her work is
   "good enough"; nurse visits clustered the day before assessments; a
   teacher observation about crying before a test she then aced.
2. **Deshawn Carter** (he/him), grade 9 — food insecurity at home.
   Attendance dips concentrated on Mondays; behavior flags cluster in the
   period right before lunch and essentially vanish afterward; engagement
   markedly higher in afternoon periods; a guardian note mentioning a shift
   change to nights; strong performance when present.
3. **Alina Restrepo** (she/her), grade 9 — newcomer, English learner, strong
   in math. Reading scores low but climbing steeply; math scores high from
   the start; AI tutor questions partly in Spanish; engagement highest in
   group and lab work, lowest in lecture; an observation about her
   translating for another student.
4. **Jordan Whitaker** (they/them), grade 10 — 504 plan for ADHD, hands-on
   learner. Behavior referrals concentrated in long lecture blocks; near-zero
   incidents in labs and studio periods; engagement inverted against
   Maya's — high in hands-on periods; a 504 plan document; assessment scores
   that swing hard by assessment format (project vs timed test).
5. **Sam Nakamura** (he/him), grade 11 — mid-year move, regression after.
   Records from a prior school through November, then a transfer; scores drop
   in December-February and partially recover by spring; engagement flat and
   low after the move; observations noting withdrawal; a guardian note about
   the move.
6. **Priya Raghunathan** (she/her), grade 11 — gifted and disengaged.
   Near-perfect test scores with missing homework; off-task behavior notes
   that are about boredom rather than conflict; AI tutor questions far beyond
   the course material; engagement low in every period except one elective.

### Verification

Write `passport/seed/test_seed.py` as a plain `assert`-based check runnable
with `python manage.py test passport.seed.test_seed` or as a standalone
Django-configured script. It must assert at minimum:
- Running the seed twice does not duplicate students
- Two runs with the same seed produce identical record counts
- Each hero student has records from at least six distinct sources
- Every date falls inside the school year and on a weekday
- Deshawn's Monday absence rate is measurably higher than other weekdays,
  and Maya's late-night AI questions actually cluster after 11pm

## Task 2 — React frontend shell

Build the frontend against **mock data**. The API does not exist yet — it is
the next phase. The goal is a working, navigable UI whose data layer can be
swapped to real endpoints by changing one module.

### Files to create

Everything under `frontend/`. Vite + React + TypeScript + Tailwind +
Recharts. Use `npm create vite@latest` conventions.

### Requirements

1. `npm run dev` serves on port 5173. `npm run build` succeeds.
2. **One data module** (`src/api/client.ts`) is the only place data comes
   from. It exports typed functions (`getMe`, `getClassrooms`,
   `getPassport(studentId)`, `askQuestion(studentId, q)`) that currently
   return mock data from `src/api/mock.ts`. Swapping to `fetch` later must
   not require touching any component.
3. Types in `src/api/types.ts` must mirror the Django models — read
   `passport/models.py` for field names and use the same snake_case keys the
   API will return. Sources are a union type matching `StudentRecord.SOURCES`.
4. Views:
   - **Login** — username/password form, posts to the client module (mocked).
     Role determines the landing view.
   - **Teacher** — tabs per classroom, roster grid, click a student to open
     their passport.
   - **Guardian** — tabs for their students.
   - **Student** — their own passport, no tabs.
   - **Passport** — the seven sections from `docs/spec.md`: overview
     (multi-voice), how they learn, performance over time (Recharts line
     chart), behavior over time, guardian input, student input, and the
     question box.
5. The question box has a microphone button using the browser-native Web
   Speech API (`webkitSpeechRecognition`). Feature-detect it and hide the
   button when unsupported. Do not add a speech dependency.
6. Mock data must include the six hero students from Task 1 with enough
   records to make the charts and sections look real. Match the arc
   descriptions above so the two halves line up.
7. Accessibility basics: form inputs have labels, the mic button has an
   accessible name and a pressed state, tab lists use real semantics, charts
   have a text alternative (a caption or table). Colors must not be the only
   signal for a behavior or performance trend.

### Verification

`npx tsc --noEmit` clean and `npm run build` succeeding are the gate. Also
add `src/api/client.test.ts` — a plain assert-based check (no test framework
needed; a script runnable via `npx tsx`) asserting the mock passport for each
hero student has a non-empty overview, at least one assessment record, and at
least one engagement record.

Do not build a component library, a state-management layer, a router
abstraction, or a design system. React Router plus local state is enough.
