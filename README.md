# Student Passport

A portable, holistic picture of a student that can be handed to a new teacher, a
new school, a guardian, the student themselves, or another learning tool.

Schools already hold a lot of information about a student, but it sits in
separate systems and most of it never reaches the person who needs it. Test
scores live in one place, the IEP in another, and the things a teacher actually
noticed — that a student is sharpest after lunch, that home has been hard this
month — are usually not written down at all. When a student changes teacher or
school, the next adult starts from zero.

The passport pulls those sources into one view and lets you ask questions of it.

> **All data in this repository is synthetic.** No real student information is
> used anywhere in this project.

## What it pulls together

- **Structured** — test scores, attendance, behavior records
- **Unstructured** — report cards, IEP and 504 plans, counselor and teacher notes
- **Untapped** — what a student asks an AI tutor, classroom situations, teacher
  observations about stressors outside school, and when in the day a student is
  most engaged

## The passport

- An overview drawing on every voice: teachers, guardians, and the student
- How this student likes to learn, and which strategies work
- How performance has changed over time
- What someone new needs to know about behavior
- Guardian input and student input
- A question box (speech-to-text enabled) — answers are written back as new
  records, so asking questions makes the passport better

## Views

- **Teacher** — tabs per class, click a student to open their passport
- **Guardian** — tabs for their students
- **Student** — their own passport

A single permission check gates every student-scoped endpoint. A guardian cannot
reach another family's student.

## Stack

Django + Django REST Framework + SQLite on the backend, React + Vite + TypeScript
on the frontend, Claude (`claude-opus-5`) via AWS Bedrock for the narrative
sections and the question box.

## Running it

```bash
python3.13 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

The Claude features read AWS credentials from your environment. Export an AWS
profile with Bedrock access before starting the server:

```bash
export AWS_PROFILE=dev-engineer
```

Everything except the question box works without it.

## Status

Early. Backend models and admin are in place; seed data, API, and frontend are
next.

## License

MIT — see [LICENSE](LICENSE).
