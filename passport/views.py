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
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Classroom, Guardianship, Passport, Profile, Student, StudentRecord
from .narrative import answer_question, build_sections
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
