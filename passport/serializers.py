"""Wire shapes for the API.

Field names match `frontend/src/api/types.ts` exactly, so a response can be
assigned to those types unchanged.
"""

from django.db.models import Exists, OuterRef, Subquery
from rest_framework import serializers

from .models import Classroom, Guardianship, Student, StudentRecord


def students_qs():
    """Students annotated with the pronouns the frontend prints, and whether
    a `cognitive_analysis` record is on file.

    `Student` has no pronouns column and must not gain one, so the value is
    read off whichever seeded record carries it. Missing is normal: the
    serializer then returns an empty string.
    """
    carrier = (
        StudentRecord.objects.filter(student=OuterRef('pk'), data__has_key='pronouns')
        .order_by('date')
        .values('data__pronouns')[:1]
    )
    ai_analysis = StudentRecord.objects.filter(
        student=OuterRef('pk'), source='cognitive_analysis'
    )
    return Student.objects.annotate(
        pronouns_value=Subquery(carrier),
        has_ai_analysis=Exists(ai_analysis),
    )


def display_name(user):
    """A person's name for display, or None for a system-authored record."""
    if user is None:
        return None
    return user.get_full_name().strip() or user.username


class StudentSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)
    pronouns = serializers.SerializerMethodField()
    has_ai_analysis = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = Student
        fields = [
            'id', 'first_name', 'last_name', 'name', 'grade', 'date_of_birth',
            'pronouns', 'has_ai_analysis',
        ]

    def get_pronouns(self, obj):
        return getattr(obj, 'pronouns_value', None) or ''


class StudentRecordSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model = StudentRecord
        fields = [
            'id', 'student', 'source', 'kind', 'date',
            'title', 'body', 'data', 'author', 'created_at',
        ]

    def get_author(self, obj):
        return display_name(obj.author)


class ClassroomSerializer(serializers.ModelSerializer):
    teachers = serializers.SerializerMethodField()
    students = serializers.SerializerMethodField()

    class Meta:
        model = Classroom
        fields = ['id', 'name', 'subject', 'grade', 'period', 'teachers', 'students']

    def get_teachers(self, obj):
        return [display_name(u) for u in obj.teachers.all()]

    def get_students(self, obj):
        roster = students_qs().filter(classrooms=obj)
        return StudentSerializer(roster, many=True).data


class GuardianSerializer(serializers.ModelSerializer):
    """A `Guardianship` flattened onto the student it concerns."""

    id = serializers.IntegerField(source='guardian.id', read_only=True)
    name = serializers.SerializerMethodField()

    class Meta:
        model = Guardianship
        fields = ['id', 'name', 'relationship']

    def get_name(self, obj):
        return display_name(obj.guardian)


class InputSubmissionSerializer(serializers.Serializer):
    """Body of `POST /api/students/<id>/input/`."""

    source = serializers.ChoiceField(
        choices=[StudentRecord.PARENT_INPUT, StudentRecord.STUDENT_INPUT]
    )
    title = serializers.CharField(max_length=200)
    body = serializers.CharField(max_length=8000)
