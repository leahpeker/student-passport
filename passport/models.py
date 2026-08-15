from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    """Role attached to a Django user. One role per login."""

    TEACHER = 'teacher'
    GUARDIAN = 'guardian'
    STUDENT = 'student'
    ROLES = [(TEACHER, 'Teacher'), (GUARDIAN, 'Guardian'), (STUDENT, 'Student')]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=16, choices=ROLES)

    def __str__(self):
        return f'{self.user.username} ({self.role})'


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student')
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    grade = models.CharField(max_length=8)
    date_of_birth = models.DateField(null=True, blank=True)
    guardians = models.ManyToManyField(User, through='Guardianship', related_name='wards')

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def name(self):
        return f'{self.first_name} {self.last_name}'


class Guardianship(models.Model):
    """Many-to-many so a student can have two parents and a parent many kids."""

    guardian = models.ForeignKey(User, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    relationship = models.CharField(max_length=32, default='parent')

    class Meta:
        unique_together = [('guardian', 'student')]

    def __str__(self):
        return f'{self.guardian.username} -> {self.student} ({self.relationship})'


class Classroom(models.Model):
    name = models.CharField(max_length=64)
    subject = models.CharField(max_length=64)
    # Blank for mixed-grade classes.
    grade = models.CharField(max_length=8, blank=True)
    period = models.CharField(max_length=16, blank=True)
    teachers = models.ManyToManyField(User, related_name='classrooms')
    students = models.ManyToManyField(Student, related_name='classrooms')

    class Meta:
        ordering = ['period', 'name']

    def __str__(self):
        return f'{self.name} ({self.subject})'


class StudentRecord(models.Model):
    """Every data source lands here.

    One table instead of eight keeps the passport assembly and the
    export endpoint simple: filter by `source`, chart from `data`.
    """

    SIS = 'sis'
    ASSESSMENT = 'assessment'
    ATTENDANCE = 'attendance'
    BEHAVIOR = 'behavior'
    DOCUMENT = 'document'
    AI_TUTOR = 'ai_tutor'
    ENGAGEMENT = 'engagement'
    OBSERVATION = 'observation'
    PARENT_INPUT = 'parent_input'
    STUDENT_INPUT = 'student_input'
    QUESTION = 'question'
    APP_INTEGRATION = 'app_integration'
    SOURCES = [
        (SIS, 'Student information system'),
        (ASSESSMENT, 'Assessment'),
        (ATTENDANCE, 'Attendance'),
        (BEHAVIOR, 'Behavior'),
        (DOCUMENT, 'Document (IEP, 504, report card)'),
        (AI_TUTOR, 'AI tutor interaction'),
        (ENGAGEMENT, 'Engagement sample'),
        (OBSERVATION, 'Teacher observation'),
        (PARENT_INPUT, 'Guardian input'),
        (STUDENT_INPUT, 'Student input'),
        (QUESTION, 'Asked question'),
        (APP_INTEGRATION, 'Learning-app activity (practice or reading session)'),
    ]

    # APP_INTEGRATION rows are one per practice or reading session. `data` shape:
    #   {"app": "Fraction Fluency", "subject": "Mathematics",
    #    "duration_minutes": 18,
    #    "questions": [{"topic": "fractions - adding", "correct": true, "seconds": 22}, ...]}
    # `kind` is 'practice_session' or 'reading_session'. Every helper that reads
    # `questions` must tolerate it being absent — a session record with no
    # question breakdown is still a valid record.
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='records')
    source = models.CharField(max_length=24, choices=SOURCES)
    kind = models.CharField(max_length=64, blank=True)
    date = models.DateField()
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)
    author = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='authored_records'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [models.Index(fields=['student', 'source', 'date'])]

    def __str__(self):
        return f'{self.student} / {self.source} / {self.title}'


class Passport(models.Model):
    """Cached LLM-written narrative. Regenerated on demand."""

    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='passport')
    sections = models.JSONField(default=dict)
    generated_at = models.DateTimeField(auto_now=True)
    # Number of records the narrative was built from, so we can tell it is stale.
    record_count = models.IntegerField(default=0)

    def __str__(self):
        return f'Passport for {self.student}'


class DailyDigest(models.Model):
    """Cached LLM-written summary of one day's APP_INTEGRATION activity.

    Separate from `Passport`: the passport is the whole-year narrative,
    this is a single day's, and a student can have many. Regenerated the
    same way — on demand, or when the day's record count has drifted.
    """

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='digests')
    date = models.DateField()
    summary = models.JSONField(default=dict)
    generated_at = models.DateTimeField(auto_now=True)
    record_count = models.IntegerField(default=0)

    class Meta:
        unique_together = [('student', 'date')]
        ordering = ['-date']

    def __str__(self):
        return f'Digest for {self.student} on {self.date}'


class ClassroomDigest(models.Model):
    """Cached LLM-written summary of one classroom's day.

    The computed half of a class view — the triage per student, the topic
    rollup — is arithmetic and never cached; it is cheap enough to recompute
    on every read. Only the written half costs a model call, and that is what
    this row holds.
    """

    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='digests')
    date = models.DateField()
    summary = models.JSONField(default=dict)
    generated_at = models.DateTimeField(auto_now=True)
    # Sessions across the whole class that day, so the cache notices new work.
    record_count = models.IntegerField(default=0)

    class Meta:
        unique_together = [('classroom', 'date')]
        ordering = ['-date']

    def __str__(self):
        return f'Digest for {self.classroom} on {self.date}'
