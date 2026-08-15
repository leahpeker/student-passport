"""Turn the authored arcs in `arcs.py` into database rows.

Deterministic: every student gets its own `random.Random(seed)`, and the
sequence of calls against it is fixed, so two runs produce byte-identical
content. The global `random` module is never used.

Idempotent: users, students and classrooms are matched on their deterministic
username / name, and a student's seeded records are cleared before being
rewritten. Records with source `question` are left alone, because those are
written at runtime by someone using the app.
"""

import random
import unicodedata
from collections import Counter
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.db import transaction

from passport.models import Classroom, Guardianship, Profile, Student, StudentRecord

from . import arcs
from .arcs import (
    ARCS,
    CLASSROOMS,
    DEMO_PASSWORD,
    ENGAGEMENT_NOTES,
    FILLER_ASSESSMENT_KINDS,
    FILLER_BEHAVIOR_BODIES,
    FILLER_GUARDIANS,
    FILLER_OBSERVATION_BODIES,
    FILLER_TUTOR_BODIES,
    FILLERS,
    SCHOOL_YEAR_END,
    SCHOOL_YEAR_START,
    TEACHERS,
)

SR = StudentRecord

SUBJECT_TEACHER = {
    'Mathematics': 'ramirez',
    'Science': 'chen',
    'English': 'boyd',
    'Social Studies': 'boyd',
    'Visual Arts': 'okafor',
    'Computer Science': 'okafor',
}

GRADE_POOLS = {
    '9': ['bio', 'lit', 'hist', 'geo', 'art'],
    '10': ['alg2', 'lit', 'hist', 'art', 'cs'],
    '11': ['lit', 'hist', 'art', 'phys', 'cs'],
}

GUARDIAN_FIRST_NAMES = [
    'Angela', 'Peter', 'Ruth', 'Samuel', 'Lorraine', 'Victor',
    'Nadine', 'Emmanuel', 'Carol', 'Julian', 'Denise', 'Omar',
]


def school_days():
    """Every weekday in the school year, in order."""
    days, d = [], SCHOOL_YEAR_START
    while d <= SCHOOL_YEAR_END:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days


SCHOOL_DAYS = school_days()
DAY_SET = set(SCHOOL_DAYS)
YEAR_SPAN = (SCHOOL_YEAR_END - SCHOOL_YEAR_START).days


def weeks():
    """School days grouped into weeks. A new week starts when the weekday resets."""
    out, cur = [], []
    for d in SCHOOL_DAYS:
        if cur and d.weekday() <= cur[-1].weekday():
            out.append(cur)
            cur = []
        cur.append(d)
    if cur:
        out.append(cur)
    return out


WEEKS = weeks()


def parse_day(iso):
    """Parse an authored date and refuse anything outside the school year."""
    d = date.fromisoformat(iso)
    if d not in DAY_SET:
        raise ValueError(f'authored date {iso} is a weekend or outside the school year')
    return d


def enrolled_days(arc):
    """School days this student was on this school's roll.

    An arc may carry 'start' and/or 'end'. Every generated record — attendance,
    behaviour, engagement — is drawn from this list, so a mid-year transfer
    cannot pick up a referral from before they walked in the door.
    """
    start = parse_day(arc['start']) if arc.get('start') else SCHOOL_YEAR_START
    end = parse_day(arc['end']) if arc.get('end') else SCHOOL_YEAR_END
    return [d for d in SCHOOL_DAYS if start <= d <= end]


# ---------------------------------------------------------------------------
# Weighted picking
# ---------------------------------------------------------------------------

def _weight(d, spec):
    if not spec:
        return 1.0
    w = spec.get('weekday', {}).get(d.weekday(), 1.0)
    w *= spec.get('month', {}).get(d.month, 1.0)
    from_dom = spec.get('from_day_of_month')
    if from_dom and d.day >= from_dom[0]:
        w *= from_dom[1]
    return w


def _weighted_index(rng, weights):
    total = sum(weights)
    if total <= 0:
        return rng.randrange(len(weights))
    target = rng.random() * total
    for i, w in enumerate(weights):
        target -= w
        if target <= 0:
            return i
    return len(weights) - 1


def pick_days(rng, days, n, spec=None):
    """Sample `n` distinct days, weighted by `spec`. Returned in date order."""
    pool = list(days)
    weights = [_weight(d, spec) for d in pool]
    chosen = []
    for _ in range(min(n, len(pool))):
        i = _weighted_index(rng, weights)
        chosen.append(pool[i])
        weights[i] = 0.0
    return sorted(chosen)


def pick_key(rng, table):
    keys = list(table)
    return keys[_weighted_index(rng, [table[k] for k in keys])]


def band(rating):
    return 'low' if rating <= 2 else ('mid' if rating == 3 else 'high')


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def upsert_user(username, first, last, role):
    user, _ = User.objects.get_or_create(username=username)
    user.first_name, user.last_name = first, last
    user.email = f'{username}@example.edu'
    user.set_password(DEMO_PASSWORD)
    user.save()
    profile, created = Profile.objects.get_or_create(user=user, defaults={'role': role})
    if not created and profile.role != role:
        profile.role = role
        profile.save()
    return user


def slug(first, last):
    """ASCII, lowercase, typeable. Accented names still get a login you can type."""
    raw = unicodedata.normalize('NFKD', f'{first}.{last}').encode('ascii', 'ignore').decode()
    return ''.join(ch for ch in raw.lower() if ch.isalnum() or ch == '.')


# ---------------------------------------------------------------------------
# Record builders. Each returns a list of unsaved StudentRecord objects.
# ---------------------------------------------------------------------------

def engagement_records(student, rng, spec, rooms, teachers, enrolled=None):
    """Several samples per week across the year.

    Rating is a per-period baseline plus a linear drift across the year plus
    noise, so an arc's shape (which periods, and whether it decays or climbs)
    lives entirely in the authored data.
    """
    base, trend, jitter = spec['base'], spec.get('trend', 0.0), spec.get('jitter', 0.4)
    per_week = spec.get('per_week', 3)
    on_roll = DAY_SET if enrolled is None else set(enrolled)
    periods = sorted(base)
    out = []
    for week in WEEKS:
        days = [d for d in week if d in on_roll]
        if not days:
            continue
        for period in sorted(rng.sample(periods, min(per_week, len(periods)))):
            d = days[rng.randrange(len(days))]
            progress = (d - SCHOOL_YEAR_START).days / YEAR_SPAN
            raw = base[period] + trend * progress + rng.gauss(0, jitter)
            rating = max(1, min(5, round(raw)))
            room = rooms[period]
            notes = ENGAGEMENT_NOTES[(room['mode'], band(rating))]
            out.append(SR(
                student=student, source=SR.ENGAGEMENT, kind='period_sample', date=d,
                title=f'Period {period} engagement sample — {room["name"]}',
                body=notes[rng.randrange(len(notes))],
                data={'period': period, 'rating': rating, 'subject': room['subject']},
                author=teachers[room['teacher']],
            ))
    return out


def app_integration_records(student, rng, rooms, base, enrolled=None, per_week=1):
    """Practice/reading-app sessions, one dominant topic per session so a
    topic accumulates enough attempts to be worth flagging.

    Driven by the same per-period baseline that shapes engagement, rather
    than a second hand-authored curve: a period that is already strong or
    weak for a student looks the same way here too. A global tendency, not a
    model of learning — the point is a real, checkable signal to synthesize
    from, not a simulation.
    """
    on_roll = DAY_SET if enrolled is None else set(enrolled)
    periods = [p for p in sorted(rooms) if rooms[p]['subject'] in arcs.APP_TOPICS]
    if not periods:
        return []
    topic_cursor = {}
    out = []
    for week in WEEKS:
        days = [d for d in week if d in on_roll]
        if not days:
            continue
        for period in sorted(rng.sample(periods, min(per_week, len(periods)))):
            room = rooms[period]
            subject = room['subject']
            topics = arcs.APP_TOPICS[subject]
            d = days[rng.randrange(len(days))]
            rating = base.get(period, 3.0)
            accuracy = max(0.2, min(0.97, 0.32 + 0.13 * rating))
            pace = max(12, min(95, 70 - 9 * rating))
            n = rng.randint(8, 14)
            idx = topic_cursor.get(period, 0)
            topic = topics[idx % len(topics)]
            topic_cursor[period] = idx + 1

            questions = []
            for _ in range(n):
                seconds = max(4, round(rng.gauss(pace, pace * 0.25)))
                questions.append({
                    'topic': topic, 'correct': rng.random() < accuracy, 'seconds': seconds,
                })
            correct = sum(1 for q in questions if q['correct'])
            duration = round(sum(q['seconds'] for q in questions) / 60, 1)
            app_name = arcs.APP_NAME.get(subject, 'Practice App')
            kind = 'reading_session' if subject in arcs.READING_SUBJECTS else 'practice_session'
            out.append(SR(
                student=student, source=SR.APP_INTEGRATION, kind=kind, date=d,
                title=f'{app_name} — {topic} ({correct}/{n})',
                data={'app': app_name, 'subject': subject,
                      'duration_minutes': duration, 'questions': questions},
            ))
    return out


def attendance_records(student, rng, spec, enrolled=None, in_school=()):
    """`in_school` are days an authored record already puts the student in the
    building, so a full-day absence can never contradict one."""
    days_on_roll = SCHOOL_DAYS if enrolled is None else enrolled
    absences = pick_days(rng, [d for d in days_on_roll if d not in in_school],
                         spec.get('count', 0), spec.get('weights'))
    remaining = [d for d in days_on_roll if d not in set(absences)]
    tardies = pick_days(rng, remaining, spec.get('tardies', 0), spec.get('tardy_weights'))
    out = []
    for d in absences:
        out.append(SR(
            student=student, source=SR.ATTENDANCE, kind='absence', date=d,
            title='Absent — full day',
            body='Marked absent for all periods. No note received from home.',
            data={'periods_missed': 8, 'present': 0},
        ))
    for d in tardies:
        minutes = rng.choice([4, 7, 11, 16, 23, 31])
        out.append(SR(
            student=student, source=SR.ATTENDANCE, kind='tardy', date=d,
            title=f'Late to period 1 by {minutes} minutes',
            body=f'Arrived {minutes} minutes into period 1. Marked tardy, not absent.',
            data={'minutes_late': minutes, 'periods_missed': 0, 'present': 1},
        ))

    absent_set, tardy_set = set(absences), set(tardies)
    months = {}
    for d in days_on_roll:
        months.setdefault((d.year, d.month), []).append(d)
    for (_, _), days in months.items():
        absent = sum(1 for d in days if d in absent_set)
        tardy = sum(1 for d in days if d in tardy_set)
        last = days[-1]
        out.append(SR(
            student=student, source=SR.ATTENDANCE, kind='monthly_summary', date=last,
            title=f'Attendance summary — {last:%B %Y}',
            body=f'{len(days) - absent} of {len(days)} school days present, '
                 f'{absent} absent, {tardy} tardy.',
            data={'enrolled_days': len(days), 'present': len(days) - absent,
                  'absent': absent, 'tardy': tardy,
                  'rate': round((len(days) - absent) / len(days), 3)},
        ))
    return out


def behavior_records(student, rng, spec, rooms, teachers, enrolled=None):
    days = pick_days(rng, SCHOOL_DAYS if enrolled is None else enrolled,
                     spec.get('count', 0), spec.get('weights'))
    period_weights = {p: w for p, w in spec['period_weights'].items() if p in rooms}
    bodies = spec['bodies']
    kind, severity = spec.get('kind', 'minor'), spec.get('severity', 1)
    out = []
    for d in days:
        period = pick_key(rng, period_weights)
        room = rooms[period]
        out.append(SR(
            student=student, source=SR.BEHAVIOR, kind=kind, date=d,
            title=f'Behaviour note — period {period}, {room["name"]}',
            body=bodies[rng.randrange(len(bodies))],
            data={'period': period, 'severity': severity},
            author=teachers[room['teacher']],
        ))
    return out


def assessment_records(student, entries, teachers, enrolled=None):
    """Scores sat before the student joined came in on a transfer file, so no
    teacher here can be their author."""
    first_day = SCHOOL_YEAR_START if enrolled is None else enrolled[0]
    out = []
    for e in entries:
        data = {'score': e['score'], 'max': 100, 'percent': e['score'],
                'format': e['format'], 'subject': e['subject']}
        data.update(e.get('data', {}))
        d = parse_day(e['date'])
        out.append(SR(
            student=student, source=SR.ASSESSMENT, kind=e['format'],
            date=d, title=f'{e["kind"]} — {e["subject"]}',
            body=e.get('body', ''), data=data,
            author=teachers.get(SUBJECT_TEACHER.get(e['subject'])) if d >= first_day else None,
        ))
    return out


def tutor_records(student, rng, authored, fill):
    out = []
    for e in authored:
        out.append(SR(
            student=student, source=SR.AI_TUTOR, kind='tutor_session',
            date=parse_day(e['date']),
            title=f'AI tutor session, {e["hour"]:02d}:{e["minute"]:02d}',
            body=e['body'], data={'hour': e['hour'], 'minute': e['minute']},
        ))
    if fill:
        bodies = fill['bodies']
        for d in pick_days(rng, SCHOOL_DAYS, fill['count'], fill.get('weights')):
            hour = pick_key(rng, fill['hour_weights'])
            minute = rng.randrange(60)
            out.append(SR(
                student=student, source=SR.AI_TUTOR, kind='tutor_session', date=d,
                title=f'AI tutor session, {hour:02d}:{minute:02d}',
                body=bodies[rng.randrange(len(bodies))],
                data={'hour': hour, 'minute': minute},
            ))
    return out


DEFAULT_PRONOUNS = 'they/them'


def with_pronouns(entries, pronouns):
    """Hang the student's pronouns off their enrolment record.

    The model has no column for it and prose is the wrong place for a
    structured attribute, so it rides in the enrolment record's `data`, which
    is where readers of the file look for who this student is.
    """
    return [dict(e, data={**e.get('data', {}), 'pronouns': pronouns})
            if e.get('kind') == 'enrollment' else e
            for e in entries]


def cite_attendance(entries, attendance):
    """Fill `{absences}` / `{tardies}` in an authored body with the real counts
    up to that record's own date, so a report card cannot cite a number the
    generator did not produce."""
    out = []
    for e in entries:
        if '{absences}' in e['body'] or '{tardies}' in e['body']:
            upto = date.fromisoformat(e['date'])
            n = Counter(r.kind for r in attendance if r.date <= upto)
            e = dict(e, body=e['body'].format(absences=n['absence'], tardies=n['tardy']))
        out.append(e)
    return out


def simple_records(student, entries, source, author=None, authors=None):
    """Authored free-text records. `authors` indexes an arc's guardian list."""
    out = []
    for e in entries:
        who = authors[e['author']] if authors is not None else author
        out.append(SR(
            student=student, source=source, kind=e.get('kind', ''),
            date=parse_day(e['date']), title=e['title'], body=e['body'],
            data=e.get('data', {}), author=who,
        ))
    return out


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------

def reset_seeded():
    """Drop everything the seeder owns. Users with a Profile plus all classrooms.

    Students, guardianships and records cascade from the users.
    """
    Classroom.objects.all().delete()
    User.objects.filter(profile__isnull=False).delete()


@transaction.atomic
def run(reset=False):
    if reset:
        reset_seeded()

    students = {}          # arc/filler key -> Student
    enrolment = {}         # classroom code -> [Student]
    guardian_users = {}    # (first, last) -> User
    logins = []            # (username, role, display name)

    teachers = {}
    for t in TEACHERS:
        username = f't.{slug(t["first"], t["last"])}'
        teachers[t['key']] = upsert_user(username, t['first'], t['last'], Profile.TEACHER)
        rooms_taught = [c['name'] for c in CLASSROOMS if c['teacher'] == t['key']]
        logins.append((username, 'teacher',
                       f'{t["first"]} {t["last"]} — {", ".join(rooms_taught)}'))

    rooms = {}
    for c in CLASSROOMS:
        room, _ = Classroom.objects.get_or_create(name=c['name'])
        room.subject, room.grade, room.period = c['subject'], c['grade'], str(c['period'])
        room.save()
        room.teachers.set([teachers[c['teacher']]])
        rooms[c['code']] = room
    by_code = {c['code']: c for c in CLASSROOMS}

    def make_student(key, first, last, grade, dob=None):
        username = f's.{slug(first, last)}'
        user = upsert_user(username, first, last, Profile.STUDENT)
        student, _ = Student.objects.update_or_create(
            user=user,
            defaults={'first_name': first, 'last_name': last, 'grade': grade,
                      'date_of_birth': date.fromisoformat(dob) if dob else None},
        )
        students[key] = student
        logins.append((username, 'student', f'{first} {last}, grade {grade}'))
        return student

    def make_guardian(first, last, relationship, student):
        user = guardian_users.get((first, last))
        if user is None:
            username = f'g.{slug(first, last)}'
            user = upsert_user(username, first, last, Profile.GUARDIAN)
            guardian_users[(first, last)] = user
            logins.append((username, 'guardian', f'{first} {last}'))
        Guardianship.objects.get_or_create(
            guardian=user, student=student, defaults={'relationship': relationship},
        )
        return user

    def enrol(student, codes):
        for code in codes:
            enrolment.setdefault(code, []).append(student)
        return {by_code[c]['period']: by_code[c] for c in codes}

    records = []
    extra_guardianships = []   # (guardian_user, relationship, filler_key)

    # --- hero arcs ---------------------------------------------------------
    for arc in ARCS:
        rng = random.Random(arc['seed'])
        student = make_student(arc['key'], arc['first'], arc['last'], arc['grade'], arc['dob'])
        period_rooms = enrol(student, arc['classrooms'])

        arc_guardians = []
        for g in arc['guardians']:
            user = make_guardian(g['first'], g['last'], g['relationship'], student)
            arc_guardians.append(user)
            for other in g.get('also_guardian_of', []):
                extra_guardianships.append((user, g['relationship'], other))

        enrolled = enrolled_days(arc)
        # Days an authored record puts them in the building: a nurse saw them, a
        # teacher watched them work, they sat a paper. None can also be a full-day
        # absence. Homework-completion rows are period summaries, not a day.
        in_school = (
            {parse_day(e['date']) for e in arc.get('sis', [])
             if e.get('kind') == 'health_office'}
            | {parse_day(e['date']) for e in arc.get('observations', [])}
            | {parse_day(e['date']) for e in arc.get('assessments', [])
               if e['format'] != 'homework'}
        )

        attendance = attendance_records(student, rng, arc.get('absences', {}), enrolled,
                                        in_school)
        records += simple_records(student, with_pronouns(arc.get('sis', []), arc['pronouns']),
                                  SR.SIS)
        records += assessment_records(student, arc.get('assessments', []), teachers, enrolled)
        records += attendance
        records += behavior_records(student, rng, arc['behavior'], period_rooms, teachers,
                                    enrolled)
        records += simple_records(
            student, cite_attendance(arc.get('documents', []), attendance), SR.DOCUMENT)
        records += tutor_records(student, rng, arc.get('ai_tutor', []),
                                 arc.get('ai_tutor_fill'))
        records += engagement_records(student, rng, arc['engagement'], period_rooms, teachers,
                                      enrolled)
        records += app_integration_records(student, rng, period_rooms, arc['engagement']['base'],
                                           enrolled, per_week=2)
        for e in arc.get('observations', []):
            records.append(SR(
                student=student, source=SR.OBSERVATION, kind=e.get('kind', 'note'),
                date=parse_day(e['date']), title=e['title'], body=e['body'],
                author=teachers[e['teacher']],
            ))
        records += simple_records(student, arc.get('parent_input', []), SR.PARENT_INPUT,
                                  authors=arc_guardians)
        records += simple_records(student, arc.get('student_input', []), SR.STUDENT_INPUT,
                                  author=student.user)

    # --- filler students ---------------------------------------------------
    for i, f in enumerate(FILLERS):
        rng = random.Random(2000 + i)
        student = make_student(f['key'], f['first'], f['last'], f['grade'])
        pool = GRADE_POOLS[f['grade']]
        codes = sorted(rng.sample(pool, rng.randint(4, 5)), key=lambda c: by_code[c]['period'])
        period_rooms = enrol(student, codes)
        records += filler_records(student, rng, period_rooms, teachers, f)

    shared = {g_student for g in FILLER_GUARDIANS for g_student in g['students']}
    for g in FILLER_GUARDIANS:
        for key in g['students']:
            make_guardian(g['first'], g['last'], g['relationship'], students[key])
    for user, relationship, key in extra_guardianships:
        Guardianship.objects.get_or_create(
            guardian=user, student=students[key], defaults={'relationship': relationship},
        )
        shared.add(key)
    for i, f in enumerate(FILLERS):
        if f.get('guardian', 'auto') is None or f['key'] in shared:
            continue
        rng = random.Random(3000 + i)
        first = GUARDIAN_FIRST_NAMES[rng.randrange(len(GUARDIAN_FIRST_NAMES))]
        make_guardian(first, f['last'], rng.choice(['mother', 'father', 'guardian']),
                      students[f['key']])

    for code, roster in enrolment.items():
        rooms[code].students.set(roster)

    # --- write records -----------------------------------------------------
    # Mark what the seeder owns, then replace only that. Anything written at
    # runtime — a question asked in the demo, a note a guardian or student
    # added — carries no marker and survives a reseed.
    for record in records:
        record.data = {**(record.data or {}), 'seeded': True}
    StudentRecord.objects.filter(
        student__in=students.values(), data__seeded=True).delete()
    StudentRecord.objects.bulk_create(records, batch_size=500)

    return {
        'students': len(students),
        'heroes': len(ARCS),
        'teachers': len(teachers),
        'guardians': len(guardian_users),
        'classrooms': len(rooms),
        'records': len(records),
        'logins': logins,
        'hero_keys': [a['key'] for a in ARCS],
    }


def filler_records(student, rng, period_rooms, teachers, f):
    """Light but plausible records, so a roster is not six students and 24 ghosts."""
    out = [SR(
        student=student, source=SR.SIS, kind='enrollment', date=SCHOOL_YEAR_START,
        title=f'Enrolled, grade {f["grade"]}',
        body='Continuing student. Schedule: periods '
             + ', '.join(str(p) for p in sorted(period_rooms)) + '.',
        data={'pronouns': f.get('pronouns', DEFAULT_PRONOUNS)},
    )]

    baseline = rng.randint(62, 95)
    spread = [SCHOOL_DAYS[int(len(SCHOOL_DAYS) * x)] for x in (0.08, 0.22, 0.36, 0.55, 0.72, 0.9)]
    for d, (subject, kind, fmt) in zip(spread, FILLER_ASSESSMENT_KINDS):
        score = max(35, min(100, round(baseline + rng.gauss(0, 6))))
        out.append(SR(
            student=student, source=SR.ASSESSMENT, kind=fmt, date=d,
            title=f'{kind} — {subject}', body='',
            data={'score': score, 'max': 100, 'percent': score,
                  'format': fmt, 'subject': subject},
            author=teachers.get(SUBJECT_TEACHER.get(subject)),
        ))

    out += attendance_records(student, rng, {'count': rng.randint(2, 7),
                                             'tardies': rng.randint(0, 5)})

    base = {p: round(rng.uniform(2.6, 4.4), 2) for p in period_rooms}
    out += engagement_records(student, rng,
                              {'base': base, 'trend': rng.uniform(-0.5, 0.6),
                               'jitter': 0.45, 'per_week': 1},
                              period_rooms, teachers)
    out += app_integration_records(student, rng, period_rooms, base, per_week=1)

    if rng.random() < 0.55:
        out += behavior_records(
            student, rng,
            {'count': rng.randint(1, 3), 'kind': 'minor', 'severity': 1,
             'period_weights': {p: 1.0 for p in period_rooms},
             'bodies': FILLER_BEHAVIOR_BODIES},
            period_rooms, teachers)

    for _ in range(rng.randint(1, 2)):
        d = SCHOOL_DAYS[rng.randrange(len(SCHOOL_DAYS))]
        period = sorted(period_rooms)[rng.randrange(len(period_rooms))]
        room = period_rooms[period]
        out.append(SR(
            student=student, source=SR.OBSERVATION, kind='note', date=d,
            title=f'Observation — period {period}, {room["name"]}',
            body=FILLER_OBSERVATION_BODIES[rng.randrange(len(FILLER_OBSERVATION_BODIES))],
            author=teachers[room['teacher']],
        ))

    for d in pick_days(rng, SCHOOL_DAYS, rng.randint(0, 3)):
        hour = rng.choice([16, 17, 18, 19, 20])
        minute = rng.randrange(60)
        out.append(SR(
            student=student, source=SR.AI_TUTOR, kind='tutor_session', date=d,
            title=f'AI tutor session, {hour:02d}:{minute:02d}',
            body=FILLER_TUTOR_BODIES[rng.randrange(len(FILLER_TUTOR_BODIES))],
            data={'hour': hour, 'minute': minute},
        ))

    out.append(SR(
        student=student, source=SR.DOCUMENT, kind='report_card',
        date=parse_day('2026-01-16'), title='Semester 1 report card',
        body='Grades on file for all enrolled periods. No teacher comment recorded.',
    ))
    return out


# Keep a reference so `arcs` is importable from here for callers and tests.
__all__ = ['run', 'reset_seeded', 'school_days', 'SCHOOL_DAYS', 'arcs']
