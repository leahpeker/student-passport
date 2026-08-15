"""The API.

Session auth, `IsAuthenticated` everywhere except login and logout.

Every student-scoped endpoint goes through `visible_student()`, which calls
`can_view_student()` and raises 404 — not 403 — when the check fails, so the
API never confirms that a student it will not show you exists.

CSRF: DRF's `SessionAuthentication` enforces CSRF on unsafe methods. `login/`
and `me/` set the `csrftoken` cookie and also return the token in the body, so
a browser client can send `X-CSRFToken` on every POST. See `docs` in the task
report for exactly what the frontend must send.
"""

from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.http import Http404
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from . import narrative
from .models import (
    Classroom,
    ClassroomDigest,
    DailyDigest,
    Guardianship,
    Passport,
    Profile,
    Student,
    StudentRecord,
)
from .narrative import answer_question, build_digest, build_sections
from .serializers import (
    ClassroomSerializer,
    GuardianSerializer,
    InputSubmissionSerializer,
    StudentRecordSerializer,
    StudentSerializer,
    students_qs,
)

# A teacher's note about a student's home life reads very differently to the
# student it is about. The frontend hides these; this is the real boundary.
HIDDEN_FROM_STUDENT = (StudentRecord.BEHAVIOR, StudentRecord.OBSERVATION)

# What a role may contribute, and under which source.
INPUT_BY_ROLE = {
    Profile.GUARDIAN: (StudentRecord.PARENT_INPUT, 'guardian note'),
    Profile.STUDENT: (StudentRecord.STUDENT_INPUT, 'student note'),
}


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------

def role_of(user):
    profile = getattr(user, 'profile', None)
    return profile.role if profile else None


def visible_students(user):
    """Every student this user may reach. The one definition of reach."""
    role = role_of(user)
    if role == Profile.TEACHER:
        return students_qs().filter(classrooms__teachers=user).distinct()
    if role == Profile.GUARDIAN:
        return students_qs().filter(guardians=user).distinct()
    if role == Profile.STUDENT:
        return students_qs().filter(user=user)
    return students_qs().none()


def can_view_student(user, student):
    """Teacher: their classrooms. Guardian: their wards. Student: themselves."""
    return visible_students(user).filter(pk=student.pk).exists()


def visible_classrooms(user):
    """Teachers see the classrooms they teach. Nobody else sees any."""
    if role_of(user) == Profile.TEACHER:
        return user.classrooms.all()
    return Classroom.objects.none()


def visible_student(request, pk):
    """The student, or 404 — including when the caller simply may not see them."""
    student = students_qs().filter(pk=pk).first()
    if student is None or not can_view_student(request.user, student):
        raise Http404
    return student


def visible_records(user, student):
    """The student's records, minus anything their role must not read.

    Answers written for an adult quote the records that adult can see, so a
    student reads back only the questions they asked themselves.
    """
    records = student.records.select_related('author')
    if role_of(user) == Profile.STUDENT:
        records = records.exclude(source__in=HIDDEN_FROM_STUDENT).exclude(
            Q(source=StudentRecord.QUESTION) & ~Q(author=user)
        )
    return records


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

def me_payload(request):
    user = request.user
    student = Student.objects.filter(user=user).first()
    return {
        'id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'role': role_of(user),
        'student_id': student.id if student else None,
        'students': StudentSerializer(visible_students(user), many=True).data,
        'classrooms': ClassroomSerializer(
            visible_classrooms(user).prefetch_related('teachers'), many=True
        ).data,
        # Additive: lets a cross-site frontend send X-CSRFToken without reading
        # the cookie. Same value as the csrftoken cookie set on this response.
        'csrf_token': get_token(request),
    }


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def login_view(request):
    user = authenticate(
        request,
        username=(request.data.get('username') or '').strip(),
        password=request.data.get('password') or '',
    )
    if user is None:
        return Response(
            {'detail': 'That username and password do not match.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    login(request, user)
    return Response(me_payload(request))


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def logout_view(request):
    """Always succeeds, so the client can always get back to a signed-out state."""
    logout(request)
    return Response({'detail': 'Signed out.'})


@api_view(['GET'])
def me(request):
    return Response(me_payload(request))


@api_view(['GET'])
def classrooms(request):
    rooms = visible_classrooms(request.user).prefetch_related('teachers')
    return Response(ClassroomSerializer(rooms, many=True).data)


# ---------------------------------------------------------------------------
# Passport
# ---------------------------------------------------------------------------

def cached_sections(student, refresh=False):
    """(sections, generated_at, record_count) for the student's passport.

    Regenerated on `refresh`, when nothing is cached, or when the record count
    has drifted. Questions are excluded from that count: `ask/` writes one on
    every call and the narrative is not built from them, so counting them would
    make the passport permanently stale and re-run the model on every read.

    A fallback narrative is never cached, so the real one is written the moment
    a Bedrock key appears.
    """
    row, _ = Passport.objects.get_or_create(student=student)
    records = list(student.records.select_related('author'))
    narrated = [r for r in records if r.source != StudentRecord.QUESTION]
    if not refresh and row.sections and row.record_count == len(narrated):
        return row.sections, row.generated_at, row.record_count

    sections, from_model = build_sections(student, narrated)
    if not from_model:
        return sections, timezone.now(), len(narrated)
    row.sections = sections
    row.record_count = len(narrated)
    row.save()
    return row.sections, row.generated_at, row.record_count


def passport_payload(request, student, with_records):
    refresh = request.query_params.get('refresh') in ('1', 'true', 'yes')
    sections, generated_at, record_count = cached_sections(student, refresh=refresh)
    if role_of(request.user) == Profile.STUDENT:
        sections = {**sections, 'behavior': ''}

    guardianships = Guardianship.objects.filter(student=student).select_related('guardian')
    payload = {
        'student': StudentSerializer(student).data,
        'guardians': GuardianSerializer(guardianships, many=True).data,
        'sections': sections,
        'generated_at': generated_at,
        'record_count': record_count,
    }
    if with_records:
        payload['records'] = StudentRecordSerializer(
            visible_records(request.user, student), many=True
        ).data
    return payload


@api_view(['GET'])
def passport(request, pk):
    return Response(passport_payload(request, visible_student(request, pk), with_records=False))


@api_view(['GET'])
def export(request, pk):
    """The whole passport, records included, for handing to another tool."""
    return Response(passport_payload(request, visible_student(request, pk), with_records=True))


@api_view(['GET'])
def records(request, pk):
    student = visible_student(request, pk)
    found = visible_records(request.user, student)
    source = request.query_params.get('source')
    if source:
        # An unknown source is not an error; it simply matches nothing.
        found = found.filter(source=source)
    return Response(StudentRecordSerializer(found, many=True).data)


# ---------------------------------------------------------------------------
# Writes
# ---------------------------------------------------------------------------

@api_view(['POST'])
def ask(request, pk):
    student = visible_student(request, pk)
    question = (request.data.get('question') or '').strip()
    if not question:
        return Response({'detail': 'A question is required.'}, status=status.HTTP_400_BAD_REQUEST)

    # Prior questions are left out so answers stay grounded in source records
    # rather than in earlier answers.
    consulted = list(
        visible_records(request.user, student).exclude(source=StudentRecord.QUESTION)
    )
    row = Passport.objects.filter(student=student).first()
    answer, cited, from_model = answer_question(
        student, question, consulted,
        sections=row.sections if row else None,
        role=role_of(request.user) or 'reader',
    )

    record = StudentRecord.objects.create(
        student=student,
        source=StudentRecord.QUESTION,
        kind='asked question',
        date=timezone.localdate(),
        title=question[:200],
        body=answer,
        data={
            'question': question,
            'cited_record_ids': cited,
            'records_consulted': len(consulted),
            'ai': from_model,
        },
        author=request.user,
    )
    return Response({
        'record': StudentRecordSerializer(record).data,
        'question': question,
        'answer': answer,
        'cited_record_ids': cited,
    })


# ---------------------------------------------------------------------------
# Daily digest — a single day's APP_INTEGRATION activity, not the passport
# ---------------------------------------------------------------------------

def _digest_day(student, requested):
    """`requested` (an ISO date string) if it parses, else the most recent
    date this student has app-integration activity on."""
    if requested:
        parsed = parse_date(requested)
        if parsed:
            return parsed
    return (
        student.records.filter(source=StudentRecord.APP_INTEGRATION)
        .order_by('-date').values_list('date', flat=True).first()
    )


def cached_digest(student, day, refresh=False):
    """(summary, generated_at, record_count) for one student, one day.

    Same regeneration policy as the passport: refresh, nothing cached, or the
    day's record count has drifted. That count is the day's app sessions only,
    so a record written elsewhere in the file does not re-run the model.

    `build_digest` gets the whole file rather than the day's app rows. The
    triage stays computed from app data alone, but the reason behind it
    usually sits in another source, and that is what the narrative is for. It
    splits the day from its prior baseline itself, so a digest never compares
    a pace against a future the student has not lived yet.
    """
    row, _ = DailyDigest.objects.get_or_create(student=student, date=day)
    day_count = student.records.filter(
        source=StudentRecord.APP_INTEGRATION, date=day
    ).count()
    if not refresh and row.summary and row.record_count == day_count:
        return row.summary, row.generated_at, row.record_count

    # Questions are excluded for the same reason the passport excludes them:
    # the narrative must not be built out of earlier narratives.
    records = list(
        student.records.select_related('author').exclude(source=StudentRecord.QUESTION)
    )
    summary, from_model = build_digest(student, records, day)
    if not from_model:
        return summary, timezone.now(), day_count
    row.summary = summary
    row.record_count = day_count
    row.save()
    return row.summary, row.generated_at, row.record_count


@api_view(['GET'])
def digest(request, pk):
    """?date=YYYY-MM-DD, defaulting to the student's most recent day of app
    activity. ?refresh=1 forces regeneration. A student with no app activity
    at all gets a placeholder, not an error — tolerant by design.

    Teachers only. The narrative is written from the whole file, so it can
    quote a behaviour entry or an observation — the two sources a student may
    not read. One prose blob has no field to blank the way the passport
    blanks `sections['behavior']`, so the boundary has to be the endpoint.
    404, not 403, to match every other student-scoped view here.
    """
    if role_of(request.user) != Profile.TEACHER:
        raise Http404
    student = visible_student(request, pk)
    day = _digest_day(student, request.query_params.get('date'))
    if day is None:
        return Response({
            'student_id': student.id,
            'date': None,
            'generated_at': None,
            'record_count': 0,
            'action': narrative.ACTION_WATCH,
            'headline': f'No app activity is on file for {student.first_name} yet.',
            'narrative': '',
            'topics': [],
            'flags': [],
        })

    refresh = request.query_params.get('refresh') in ('1', 'true', 'yes')
    summary, generated_at, record_count = cached_digest(student, day, refresh=refresh)
    return Response({
        'student_id': student.id,
        'generated_at': generated_at,
        'record_count': record_count,
        **summary,
    })


# ---------------------------------------------------------------------------
# Classroom view — the same day, one altitude up
# ---------------------------------------------------------------------------

def visible_classroom(request, pk):
    """The classroom, or 404 — including when the caller does not teach it.

    Teachers only, for the same reason the student digest is: the roster
    carries every student's triage and the shape of their work.
    """
    room = visible_classrooms(request.user).filter(pk=pk).prefetch_related('students').first()
    if room is None:
        raise Http404
    return room


def class_rows(classroom, day):
    """Every student on the roll with their computed triage for `day`.

    One query for the whole class's app records rather than one per student,
    and no model call at all — this is what makes a thirty-student roster
    render immediately.
    """
    # students_qs() carries the pronouns annotation, so a class narrative can
    # refer to a student the way the school does instead of guessing from a name.
    students = list(students_qs().filter(classrooms=classroom))
    by_student = {student.id: [] for student in students}
    records = StudentRecord.objects.filter(
        student__in=students, source=StudentRecord.APP_INTEGRATION, date__lte=day
    ).only('student_id', 'date', 'title', 'data')
    for record in records:
        by_student[record.student_id].append(record)
    return narrative.sort_rows([
        {'student': student, **narrative.student_day_triage(by_student[student.id], day)}
        for student in students
    ])


def _class_day(classroom, requested):
    """`requested` if it parses, else the most recent date anyone on this roll
    has app activity on."""
    if requested:
        parsed = parse_date(requested)
        if parsed:
            return parsed
    return (
        StudentRecord.objects.filter(
            student__classrooms=classroom, source=StudentRecord.APP_INTEGRATION
        ).order_by('-date').values_list('date', flat=True).first()
    )


def cached_class_digest(classroom, day, rows, refresh=False):
    """(summary, generated_at, record_count) for one classroom, one day.

    Drift is measured on sessions across the whole roll, so a student
    finishing more work after the digest was written regenerates it.
    """
    row, _ = ClassroomDigest.objects.get_or_create(classroom=classroom, date=day)
    sessions = sum(r['sessions'] for r in rows)
    if not refresh and row.summary and row.record_count == sessions:
        return row.summary, row.generated_at, row.record_count

    summary, from_model = narrative.build_class_digest(classroom, rows, day)
    if not from_model:
        return summary, timezone.now(), sessions
    row.summary = summary
    row.record_count = sessions
    row.save()
    return row.summary, row.generated_at, row.record_count


@api_view(['GET'])
def classroom_digest(request, pk):
    """?date=YYYY-MM-DD, defaulting to the most recent day anyone on this roll
    has app activity. ?refresh=1 forces regeneration."""
    classroom = visible_classroom(request, pk)
    day = _class_day(classroom, request.query_params.get('date'))
    if day is None:
        return Response({
            'date': None,
            'generated_at': None,
            'record_count': 0,
            'classroom': ClassroomSerializer(classroom).data,
            'counts': {action: 0 for action in narrative.ACTIONS},
            'no_activity': [],
            'topics': [],
            'students': [],
            'headline': f'No app activity is on file for {classroom.name} yet.',
            'narrative': '',
            'focus': [],
        })

    rows = class_rows(classroom, day)
    refresh = request.query_params.get('refresh') in ('1', 'true', 'yes')
    summary, generated_at, record_count = cached_class_digest(
        classroom, day, rows, refresh=refresh
    )
    return Response({'generated_at': generated_at, 'record_count': record_count, **summary})


@api_view(['POST'])
def classroom_ask(request, pk):
    """One question about the class, grounded in the same computed picture the
    digest is written from."""
    classroom = visible_classroom(request, pk)
    question = (request.data.get('question') or '').strip()
    if not question:
        return Response({'detail': 'A question is required.'}, status=status.HTTP_400_BAD_REQUEST)

    day = _class_day(classroom, request.query_params.get('date'))
    if day is None:
        return Response(
            {'detail': f'No app activity is on file for {classroom.name} yet.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    rows = class_rows(classroom, day)
    cached = ClassroomDigest.objects.filter(classroom=classroom, date=day).first()
    answer, from_model = narrative.answer_class_question(
        classroom, question, rows, day, summary=cached.summary if cached else None
    )
    return Response({
        'classroom_id': classroom.id,
        'date': str(day),
        'question': question,
        'answer': answer,
        'students_consulted': len(rows),
        'ai': from_model,
    })


@api_view(['POST'])
def student_input(request, pk):
    student = visible_student(request, pk)
    submission = InputSubmissionSerializer(data=request.data)
    submission.is_valid(raise_exception=True)

    allowed = INPUT_BY_ROLE.get(role_of(request.user))
    if allowed is None or allowed[0] != submission.validated_data['source']:
        # The caller can already see this student, so there is nothing to hide.
        return Response(
            {'detail': 'Your role cannot add that kind of input.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    record = StudentRecord.objects.create(
        student=student,
        source=allowed[0],
        kind=allowed[1],
        date=timezone.localdate(),
        title=submission.validated_data['title'],
        body=submission.validated_data['body'],
        author=request.user,
    )
    return Response(StudentRecordSerializer(record).data, status=status.HTTP_201_CREATED)
