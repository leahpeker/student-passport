"""API tests.

Run: .venv/bin/python manage.py test passport.test_api

The model is mocked everywhere; nothing here reaches Bedrock. The fixture is
built by hand rather than by the seeder so these tests stay honest when the
seed data changes.

All data here is synthetic.
"""

from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase

from . import narrative
from .models import (
    Classroom,
    Guardianship,
    Passport,
    Profile,
    Student,
    StudentRecord,
)

PASSWORD = 'test-pass-12345'

FAKE_SECTIONS = {
    'overview': {'teacher_voice': 'T.', 'guardian_voice': 'G.', 'student_voice': 'S.'},
    'how_they_learn': 'Learns.',
    'performance': 'Performs.',
    'behavior': 'Behaves.',
}


def make_user(username, role, **extra):
    user = User.objects.create_user(username=username, password=PASSWORD, **extra)
    Profile.objects.create(user=user, role=role)
    return user


def make_student(first, last, grade='9'):
    user = make_user(f's.{first}'.lower(), Profile.STUDENT, first_name=first, last_name=last)
    return Student.objects.create(user=user, first_name=first, last_name=last, grade=grade)


class ApiTestCase(TestCase):
    """One school: two teachers, two students, one guardian of the first."""

    @classmethod
    def setUpTestData(cls):
        cls.teacher = make_user('t.own', Profile.TEACHER, first_name='Own', last_name='Teacher')
        cls.stranger = make_user('t.other', Profile.TEACHER, first_name='Other', last_name='Teacher')
        cls.guardian = make_user('g.one', Profile.GUARDIAN, first_name='One', last_name='Guardian')

        cls.mine = make_student('Ada', 'Lovelace')
        cls.theirs = make_student('Grace', 'Hopper')

        cls.room = Classroom.objects.create(name='Maths', subject='Maths', grade='9', period='3')
        cls.room.teachers.add(cls.teacher)
        cls.room.students.add(cls.mine)

        cls.other_room = Classroom.objects.create(name='Physics', subject='Science', period='5')
        cls.other_room.teachers.add(cls.stranger)
        cls.other_room.students.add(cls.theirs)

        Guardianship.objects.create(guardian=cls.guardian, student=cls.mine, relationship='mother')

        for student in (cls.mine, cls.theirs):
            StudentRecord.objects.create(
                student=student, source=StudentRecord.ASSESSMENT, kind='timed_test',
                date=date(2026, 3, 1), title='Unit test',
                data={'score': 88, 'subject': 'Maths', 'pronouns': 'she/her'},
            )
            StudentRecord.objects.create(
                student=student, source=StudentRecord.BEHAVIOR, kind='minor',
                date=date(2026, 3, 2), title='Off task', data={'period': 4},
            )
            StudentRecord.objects.create(
                student=student, source=StudentRecord.OBSERVATION, kind='note',
                date=date(2026, 3, 3), title='Home life',
                body='Mentioned a difficult week at home.', author=cls.teacher,
            )
            StudentRecord.objects.create(
                student=student, source=StudentRecord.ENGAGEMENT, kind='period_sample',
                date=date(2026, 3, 4), title='Period 6 sample',
                data={'period': 6, 'rating': 5},
            )

    def sign_in(self, user):
        self.assertTrue(self.client.login(username=user.username, password=PASSWORD))

    def post(self, path, body):
        return self.client.post(path, body, content_type='application/json')


class PermissionTests(ApiTestCase):
    def test_teacher_sees_own_student_and_not_a_stranger_s(self):
        self.sign_in(self.teacher)
        self.assertEqual(self.client.get(f'/api/students/{self.mine.id}/records/').status_code, 200)
        self.assertEqual(self.client.get(f'/api/students/{self.theirs.id}/records/').status_code, 404)

    def test_guardian_gets_404_for_a_student_they_do_not_guard(self):
        self.sign_in(self.guardian)
        self.assertEqual(self.client.get(f'/api/students/{self.mine.id}/records/').status_code, 200)
        for path in ('records', 'passport', 'export'):
            response = self.client.get(f'/api/students/{self.theirs.id}/{path}/')
            self.assertEqual(response.status_code, 404, path)
        self.assertEqual(
            self.post(f'/api/students/{self.theirs.id}/ask/', {'question': 'Anything?'}).status_code,
            404,
        )

    def test_student_reaches_only_themselves(self):
        self.sign_in(self.mine.user)
        self.assertEqual(self.client.get(f'/api/students/{self.mine.id}/records/').status_code, 200)
        self.assertEqual(self.client.get(f'/api/students/{self.theirs.id}/records/').status_code, 404)

        me = self.client.get('/api/me/').json()
        self.assertEqual(me['role'], 'student')
        self.assertEqual(me['student_id'], self.mine.id)
        self.assertEqual([s['id'] for s in me['students']], [self.mine.id])

    def test_missing_student_is_also_404(self):
        self.sign_in(self.teacher)
        self.assertEqual(self.client.get('/api/students/99999/records/').status_code, 404)

    def test_signed_out_callers_are_refused(self):
        response = self.client.get(f'/api/students/{self.mine.id}/records/')
        self.assertIn(response.status_code, (401, 403))

    def test_classrooms_are_teachers_only(self):
        self.sign_in(self.teacher)
        rooms = self.client.get('/api/classrooms/').json()
        self.assertEqual([r['name'] for r in rooms], ['Maths'])
        self.assertEqual([s['id'] for s in rooms[0]['students']], [self.mine.id])

        for user in (self.guardian, self.mine.user):
            self.client.logout()
            self.sign_in(user)
            self.assertEqual(self.client.get('/api/classrooms/').json(), [])


@patch('passport.narrative.complete', return_value='{"overview": {"teacher_voice": "T.", '
       '"guardian_voice": "G.", "student_voice": "S."}, "how_they_learn": "Learns.", '
       '"performance": "Performs.", "behavior": "Behaves."}')
class PassportTests(ApiTestCase):
    def test_teacher_passport_is_complete(self, _complete):
        self.sign_in(self.teacher)
        body = self.client.get(f'/api/students/{self.mine.id}/passport/').json()
        self.assertEqual(body['sections'], FAKE_SECTIONS)
        self.assertEqual(body['student']['name'], 'Ada Lovelace')
        self.assertEqual(body['student']['pronouns'], 'she/her')
        self.assertEqual([g['name'] for g in body['guardians']], ['One Guardian'])
        self.assertEqual(body['record_count'], 4)

    def test_student_passport_omits_behavior_and_observation(self, _complete):
        self.sign_in(self.mine.user)
        body = self.client.get(f'/api/students/{self.mine.id}/passport/').json()
        self.assertEqual(body['sections']['behavior'], '')
        self.assertEqual(body['sections']['how_they_learn'], 'Learns.')

        sources = {r['source'] for r in self.client.get(
            f'/api/students/{self.mine.id}/records/').json()}
        self.assertNotIn('behavior', sources)
        self.assertNotIn('observation', sources)
        self.assertIn('assessment', sources)

        exported = self.client.get(f'/api/students/{self.mine.id}/export/').json()
        self.assertNotIn('behavior', {r['source'] for r in exported['records']})

    def test_a_student_does_not_read_back_an_adult_s_question(self, _complete):
        StudentRecord.objects.create(
            student=self.mine, source=StudentRecord.QUESTION, kind='asked question',
            date=date(2026, 4, 1), title='Any behaviour pattern?',
            body='Off task in period 4.', author=self.teacher,
        )
        self.sign_in(self.mine.user)
        titles = [r['title'] for r in
                  self.client.get(f'/api/students/{self.mine.id}/records/').json()]
        self.assertNotIn('Any behaviour pattern?', titles)

        self.client.logout()
        self.sign_in(self.teacher)
        titles = [r['title'] for r in
                  self.client.get(f'/api/students/{self.mine.id}/records/').json()]
        self.assertIn('Any behaviour pattern?', titles)

    def test_cached_until_the_record_count_drifts(self, complete_mock):
        self.sign_in(self.teacher)
        path = f'/api/students/{self.mine.id}/passport/'
        self.client.get(path)
        self.client.get(path)
        self.assertEqual(complete_mock.call_count, 1)

        self.client.get(f'{path}?refresh=1')
        self.assertEqual(complete_mock.call_count, 2)

        StudentRecord.objects.create(
            student=self.mine, source=StudentRecord.PARENT_INPUT, kind='guardian note',
            date=date(2026, 4, 1), title='From home', body='Mornings are hard.',
        )
        self.client.get(path)
        self.assertEqual(complete_mock.call_count, 3)

    def test_records_filter_by_source(self, _complete):
        self.sign_in(self.teacher)
        body = self.client.get(
            f'/api/students/{self.mine.id}/records/?source=assessment').json()
        self.assertEqual([r['source'] for r in body], ['assessment'])
        self.assertEqual(
            self.client.get(f'/api/students/{self.mine.id}/records/?source=nonsense').json(), [])

    def test_export_carries_the_records(self, _complete):
        self.sign_in(self.teacher)
        body = self.client.get(f'/api/students/{self.mine.id}/export/').json()
        self.assertEqual(len(body['records']), 4)
        self.assertEqual(body['sections'], FAKE_SECTIONS)


@patch('passport.narrative.complete', return_value=(
    '{"action": "watch", "headline": "H.", "narrative": "N."}'
))
class DigestTests(ApiTestCase):
    """A separate synthesis from the passport: one day of app-integration
    activity, with an intervene / watch / on_track triage."""

    def add_session(self, student, day, topic='fractions - adding', accuracy=1.0, n=8, seconds=30):
        correct = round(n * accuracy)
        questions = [
            {'topic': topic, 'correct': i < correct, 'seconds': seconds} for i in range(n)
        ]
        return StudentRecord.objects.create(
            student=student, source=StudentRecord.APP_INTEGRATION, kind='practice_session',
            date=day, title=f'Practice — {topic}',
            data={'app': 'Numeracy Coach', 'subject': 'Maths',
                  'duration_minutes': 12, 'questions': questions},
        )

    def shaped_session(self, student, day, marks, hit_seconds=30, miss_seconds=30,
                       topic='fractions - adding'):
        """A session with an exact right/wrong sequence. `marks` is a string of
        '.' for right and 'X' for wrong, so a test reads as the shape it means."""
        questions = [
            {'topic': topic, 'correct': m == '.',
             'seconds': hit_seconds if m == '.' else miss_seconds}
            for m in marks
        ]
        return StudentRecord.objects.create(
            student=student, source=StudentRecord.APP_INTEGRATION, kind='practice_session',
            date=day, title=f'Practice — {topic}',
            data={'app': 'Numeracy Coach', 'subject': 'Maths',
                  'duration_minutes': 12, 'questions': questions},
        )

    def insights_for(self, marks, **kwargs):
        record = self.shaped_session(self.mine, date(2026, 3, 5), marks, **kwargs)
        return ' '.join(narrative.session_shape(record))

    def test_a_session_that_fades_reads_differently_from_one_that_warms_up(self, _complete):
        self.assertIn('faded across the session', self.insights_for('.....XXXXX'))
        self.assertIn('warmed up', self.insights_for('XXXXX.....'))

    def test_an_even_session_gets_no_trajectory_claim(self, _complete):
        even = self.insights_for('.X.X.X.X.X')
        self.assertNotIn('faded', even)
        self.assertNotIn('warmed up', even)

    def test_misses_running_together_are_called_out(self, _complete):
        self.assertIn('missed 4 in a row', self.insights_for('..X..XXXX.'))
        # The same score scattered is a different conversation, so no streak line.
        self.assertNotIn('in a row', self.insights_for('.X.X.X.X.X'))

    def test_slow_misses_read_as_effort_and_fast_misses_as_clicking_through(self, _complete):
        worked = self.insights_for('.....XXXXX', hit_seconds=20, miss_seconds=60)
        self.assertIn('worked at rather than rushed', worked)
        rushed = self.insights_for('.....XXXXX', hit_seconds=60, miss_seconds=15)
        self.assertIn('answered quickly rather than worked through', rushed)

    def test_a_short_session_makes_no_shape_claim(self, _complete):
        """Four questions cannot show a trajectory; do not pretend otherwise."""
        self.assertEqual(self.insights_for('.XXX'), '')

    def test_insights_reach_the_payload_and_the_prompt(self, complete_mock):
        self.shaped_session(self.mine, date(2026, 3, 5), '.....XXXXX')
        self.sign_in(self.teacher)
        body = self.client.get(
            f'/api/students/{self.mine.id}/digest/?date=2026-03-05').json()
        self.assertTrue(any('faded across the session' in i for i in body['insights']))
        self.assertIn('faded across the session', complete_mock.call_args[0][0])

    def test_defaults_to_the_most_recent_day_with_activity(self, _complete):
        self.add_session(self.mine, date(2026, 3, 1))
        self.add_session(self.mine, date(2026, 3, 10))
        self.sign_in(self.teacher)
        body = self.client.get(f'/api/students/{self.mine.id}/digest/').json()
        self.assertEqual(body['date'], '2026-03-10')

    def test_a_student_with_no_app_activity_gets_a_placeholder_not_an_error(self, _complete):
        self.sign_in(self.teacher)
        response = self.client.get(f'/api/students/{self.mine.id}/digest/')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIsNone(body['date'])
        self.assertEqual(body['action'], 'watch')
        self.assertEqual(body['flags'], [])

    def test_low_accuracy_triggers_intervene_and_a_real_flag(self, _complete):
        self.add_session(self.mine, date(2026, 3, 5), accuracy=0.0, n=8)
        self.sign_in(self.teacher)
        body = self.client.get(
            f'/api/students/{self.mine.id}/digest/?date=2026-03-05').json()
        self.assertEqual(body['action'], 'intervene')
        self.assertEqual(len(body['flags']), 1)
        self.assertEqual(body['flags'][0]['severity'], 'concern')
        self.assertEqual(body['flags'][0]['topic'], 'fractions - adding')

    def test_high_accuracy_gives_no_flags_and_reads_on_track(self, _complete):
        self.add_session(self.mine, date(2026, 3, 5), accuracy=1.0, n=8)
        self.sign_in(self.teacher)
        body = self.client.get(
            f'/api/students/{self.mine.id}/digest/?date=2026-03-05').json()
        self.assertEqual(body['flags'], [])
        self.assertEqual(body['action'], 'on_track')

    def test_too_few_attempts_never_flags(self, _complete):
        self.add_session(self.mine, date(2026, 3, 5), accuracy=0.0, n=2)
        self.sign_in(self.teacher)
        body = self.client.get(
            f'/api/students/{self.mine.id}/digest/?date=2026-03-05').json()
        self.assertEqual(body['flags'], [])

    def test_model_cannot_override_the_computed_action(self, complete_mock):
        complete_mock.return_value = (
            '{"action": "on_track", "headline": "H.", "narrative": "N."}'
        )
        self.add_session(self.mine, date(2026, 3, 5), accuracy=0.0, n=8)
        self.sign_in(self.teacher)
        body = self.client.get(
            f'/api/students/{self.mine.id}/digest/?date=2026-03-05').json()
        # The model tried to say on_track; the concern-level flag wins.
        self.assertEqual(body['action'], 'intervene')

    def test_pace_flag_compares_to_the_student_s_own_prior_baseline(self, _complete):
        self.add_session(self.mine, date(2026, 2, 1), seconds=20, n=8)
        self.add_session(self.mine, date(2026, 3, 5), seconds=60, n=8)
        self.sign_in(self.teacher)
        body = self.client.get(
            f'/api/students/{self.mine.id}/digest/?date=2026-03-05').json()
        kinds = {f['kind'] for f in body['flags']}
        self.assertIn('pace', kinds)

    def test_baseline_excludes_the_digest_day_itself(self, _complete):
        # A single day cannot be its own baseline: pace flags need history.
        self.add_session(self.mine, date(2026, 3, 5), seconds=60, n=8)
        self.sign_in(self.teacher)
        body = self.client.get(
            f'/api/students/{self.mine.id}/digest/?date=2026-03-05').json()
        self.assertEqual({f['kind'] for f in body['flags']}, set())

    def test_no_record_after_the_day_reaches_the_model(self, complete_mock):
        """A digest for a past day is written from what was known that day."""
        self.add_session(self.mine, date(2026, 3, 5), accuracy=0.0, n=8)
        StudentRecord.objects.create(
            student=self.mine, source=StudentRecord.OBSERVATION, date=date(2026, 5, 1),
            title='Later observation', body='UNSEEABLE-FUTURE-NOTE',
        )
        self.sign_in(self.teacher)
        self.client.get(f'/api/students/{self.mine.id}/digest/?date=2026-03-05')
        prompt = complete_mock.call_args[0][0]
        self.assertNotIn('UNSEEABLE-FUTURE-NOTE', prompt)

    def test_only_teachers_reach_the_digest(self, _complete):
        """The narrative draws on behaviour and observations, so it is not a
        surface a guardian or a student may read."""
        self.add_session(self.mine, date(2026, 3, 5), accuracy=0.0, n=8)
        url = f'/api/students/{self.mine.id}/digest/?date=2026-03-05'
        for user in (self.guardian, self.mine.user):
            self.sign_in(user)
            self.assertEqual(self.client.get(url).status_code, 404, f'{user} reached the digest')
        self.sign_in(self.teacher)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_a_teacher_cannot_see_a_student_they_do_not_teach(self, _complete):
        self.add_session(self.theirs, date(2026, 3, 5))
        self.sign_in(self.teacher)
        self.assertEqual(
            self.client.get(f'/api/students/{self.theirs.id}/digest/').status_code, 404)

    def test_invalid_date_falls_back_to_most_recent(self, _complete):
        self.add_session(self.mine, date(2026, 3, 1))
        self.sign_in(self.teacher)
        body = self.client.get(
            f'/api/students/{self.mine.id}/digest/?date=not-a-date').json()
        self.assertEqual(body['date'], '2026-03-01')


@patch('passport.narrative.complete', return_value=(
    '{"headline": "H.", "narrative": "N.", "focus": ["Reteach fractions to Ada"]}'
))
class ClassroomDigestTests(ApiTestCase):
    """The same day as the student digest, one altitude up: every student on
    the roll triaged, and a topic rollup across the class."""

    DAY = date(2026, 3, 5)

    def setUp(self):
        super().setUp()
        # A second student on the teacher's roll, so a class has a spread.
        self.also = make_student('Ben', 'Clarke')
        self.room.students.add(self.also)

    def session(self, student, marks, day=None, topic='fractions - adding', seconds=30):
        return StudentRecord.objects.create(
            student=student, source=StudentRecord.APP_INTEGRATION, kind='practice_session',
            date=day or self.DAY, title=f'Practice — {topic}',
            data={'app': 'Numeracy Coach', 'subject': 'Maths', 'duration_minutes': 12,
                  'questions': [{'topic': topic, 'correct': m == '.', 'seconds': seconds}
                                for m in marks]},
        )

    def get(self, **params):
        query = '&'.join(f'{k}={v}' for k, v in {'date': '2026-03-05', **params}.items())
        return self.client.get(f'/api/classrooms/{self.room.id}/digest/?{query}')

    def test_roster_counts_and_orders_worst_first(self, _complete):
        self.session(self.mine, 'XXXXXXXX')          # 0/8  -> intervene
        self.session(self.also, '........')          # 8/8  -> on_track
        self.sign_in(self.teacher)
        body = self.get().json()
        self.assertEqual(body['counts'], {'intervene': 1, 'watch': 0, 'on_track': 1})
        self.assertEqual([s['name'] for s in body['students']],
                         ['Ada Lovelace', 'Ben Clarke'])
        self.assertEqual(body['students'][0]['action'], 'intervene')

    def test_a_student_with_no_activity_is_named_but_not_counted(self, _complete):
        """No data is not a tier. Counting it as 'watch' buries the students
        who actually need something under everyone who skipped the app."""
        self.session(self.mine, '........')
        self.sign_in(self.teacher)
        body = self.get().json()
        self.assertEqual(body['counts'], {'intervene': 0, 'watch': 0, 'on_track': 1})
        self.assertEqual(body['no_activity'], ['Ben Clarke'])
        # Still on the roster, sorted below everyone with real work, and
        # carrying no tier at all rather than a misleading one.
        self.assertEqual(body['students'][-1]['name'], 'Ben Clarke')
        self.assertEqual(body['students'][-1]['sessions'], 0)
        self.assertIsNone(body['students'][-1]['action'])

    def test_the_prompt_never_labels_a_quiet_student_with_a_tier(self, complete_mock):
        self.session(self.mine, '........')
        self.sign_in(self.teacher)
        self.get()
        prompt = complete_mock.call_args[0][0]
        self.assertIn('No app activity at all today, so no triage either', prompt)
        self.assertNotIn('Ben Clarke \u2014 watch', prompt)

    def test_topic_rollup_aggregates_across_students_and_names_who_struggled(self, _complete):
        self.session(self.mine, 'XXXXXXXX')
        self.session(self.also, '....XXXX')
        self.sign_in(self.teacher)
        topic = self.get().json()['topics'][0]
        self.assertEqual(topic['topic'], 'fractions - adding')
        self.assertEqual((topic['correct'], topic['attempted']), (4, 16))
        self.assertEqual(topic['students'], 2)
        self.assertEqual(topic['struggling'], ['Ada Lovelace', 'Ben Clarke'])

    def test_the_whole_roster_costs_one_model_call(self, complete_mock):
        """The computed half is arithmetic; only the narrative costs Bedrock."""
        self.session(self.mine, 'XXXXXXXX')
        self.session(self.also, '........')
        self.sign_in(self.teacher)
        self.get()
        self.assertEqual(complete_mock.call_count, 1)

    def test_focus_and_narrative_come_from_the_model(self, _complete):
        self.session(self.mine, 'XXXXXXXX')
        self.sign_in(self.teacher)
        body = self.get().json()
        self.assertEqual(body['headline'], 'H.')
        self.assertEqual(body['focus'], ['Reteach fractions to Ada'])

    def test_a_second_read_is_cached_and_makes_no_model_call(self, complete_mock):
        self.session(self.mine, 'XXXXXXXX')
        self.sign_in(self.teacher)
        self.get()
        self.get()
        self.assertEqual(complete_mock.call_count, 1)
        self.get(refresh=1)
        self.assertEqual(complete_mock.call_count, 2)

    def test_new_work_after_the_digest_regenerates_it(self, complete_mock):
        self.session(self.mine, 'XXXXXXXX')
        self.sign_in(self.teacher)
        self.get()
        self.session(self.also, '........')
        self.get()
        self.assertEqual(complete_mock.call_count, 2)

    def test_a_teacher_cannot_reach_a_classroom_they_do_not_teach(self, _complete):
        self.sign_in(self.teacher)
        self.assertEqual(
            self.client.get(f'/api/classrooms/{self.other_room.id}/digest/').status_code, 404)

    def test_guardians_and_students_cannot_reach_a_classroom_digest(self, _complete):
        self.session(self.mine, 'XXXXXXXX')
        for user in (self.guardian, self.mine.user):
            self.sign_in(user)
            self.assertEqual(
                self.client.get(f'/api/classrooms/{self.room.id}/digest/').status_code, 404)

    def test_a_class_with_no_app_activity_gets_a_placeholder_not_an_error(self, _complete):
        self.sign_in(self.teacher)
        response = self.client.get(f'/api/classrooms/{self.room.id}/digest/')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIsNone(body['date'])
        self.assertEqual(body['counts'], {'intervene': 0, 'watch': 0, 'on_track': 0})

    def test_the_day_never_reaches_past_itself(self, _complete):
        """A past day is triaged from what was known then, not from later work."""
        self.session(self.mine, 'XXXXXXXX', day=date(2026, 3, 5))
        self.session(self.mine, '........', day=date(2026, 4, 1))
        self.sign_in(self.teacher)
        body = self.get().json()
        row = next(s for s in body['students'] if s['name'] == 'Ada Lovelace')
        self.assertEqual(row['topics'][0]['attempted'], 8)
        self.assertEqual(row['action'], 'intervene')


@patch('passport.narrative.complete', return_value='Pull Ada and Ben for fractions.')
class ClassroomAskTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        StudentRecord.objects.create(
            student=self.mine, source=StudentRecord.APP_INTEGRATION, kind='practice_session',
            date=date(2026, 3, 5), title='Practice — fractions',
            data={'app': 'Numeracy Coach', 'subject': 'Maths', 'duration_minutes': 12,
                  'questions': [{'topic': 'fractions - adding', 'correct': False, 'seconds': 30}
                                for _ in range(8)]},
        )

    def ask(self, room, question='Who should I pull for a small group?'):
        return self.post(f'/api/classrooms/{room.id}/ask/', {'question': question})

    def test_a_teacher_gets_an_answer_grounded_in_the_roster(self, _complete):
        self.sign_in(self.teacher)
        body = self.ask(self.room).json()
        self.assertEqual(body['answer'], 'Pull Ada and Ben for fractions.')
        self.assertEqual(body['students_consulted'], 1)
        self.assertTrue(body['ai'])

    def test_the_class_picture_reaches_the_prompt(self, complete_mock):
        self.sign_in(self.teacher)
        self.ask(self.room)
        prompt = complete_mock.call_args[0][0]
        self.assertIn('Ada Lovelace', prompt)
        self.assertIn('fractions - adding', prompt)

    def test_the_prompt_carries_pronouns_so_the_model_never_guesses(self, complete_mock):
        """The fixture's SIS record holds she/her for Ada."""
        self.sign_in(self.teacher)
        self.ask(self.room)
        self.assertIn('Ada Lovelace (she/her)', complete_mock.call_args[0][0])

    def test_an_empty_question_is_refused(self, _complete):
        self.sign_in(self.teacher)
        self.assertEqual(self.ask(self.room, question='  ').status_code, 400)

    def test_asking_about_another_teacher_s_class_is_404(self, _complete):
        self.sign_in(self.teacher)
        self.assertEqual(self.ask(self.other_room).status_code, 404)

    def test_guardians_and_students_cannot_ask_about_a_class(self, _complete):
        for user in (self.guardian, self.mine.user):
            self.sign_in(user)
            self.assertEqual(self.ask(self.room).status_code, 404)

    def test_class_ask_writes_no_record(self, _complete):
        """Unlike student ask/, a class question is not filed against anyone."""
        before = StudentRecord.objects.count()
        self.sign_in(self.teacher)
        self.ask(self.room)
        self.assertEqual(StudentRecord.objects.count(), before)


class AskTests(ApiTestCase):
    ANSWER = (
        'She scored 88 on the Maths unit test of 2026-03-01 and rates 5 out of 5 '
        'in period 6.\nRECORDS: {ids}'
    )

    def ask(self, student, question='When is she most engaged?'):
        return self.post(f'/api/students/{student.id}/ask/', {'question': question})

    def test_ask_writes_exactly_one_question_record(self):
        self.sign_in(self.teacher)
        ids = list(self.mine.records.values_list('id', flat=True))
        with patch('passport.narrative.complete',
                   return_value=self.ANSWER.format(ids=', '.join(map(str, ids[:2])))):
            body = self.ask(self.mine).json()

        questions = StudentRecord.objects.filter(
            student=self.mine, source=StudentRecord.QUESTION)
        self.assertEqual(questions.count(), 1)
        record = questions.get()
        self.assertEqual(record.title, 'When is she most engaged?')
        self.assertIn('88', record.body)
        self.assertEqual(record.data['question'], 'When is she most engaged?')
        self.assertEqual(record.data['cited_record_ids'], ids[:2])
        self.assertEqual(record.author, self.teacher)

        self.assertEqual(body['record']['id'], record.id)
        self.assertEqual(body['cited_record_ids'], ids[:2])
        self.assertNotIn('RECORDS:', body['answer'])
        self.assertEqual(StudentRecord.objects.filter(
            student=self.theirs, source=StudentRecord.QUESTION).count(), 0)

    def test_prompt_carries_this_student_s_records(self):
        self.sign_in(self.teacher)
        with patch('passport.narrative.complete', return_value='Answer.') as complete_mock:
            self.ask(self.mine)
        prompt = complete_mock.call_args.args[0]
        self.assertIn('Ada Lovelace', prompt)
        self.assertIn('Unit test', prompt)
        self.assertIn('period 6', prompt)
        self.assertNotIn('Grace Hopper', prompt)

    def test_cited_ids_are_filtered_to_records_we_supplied(self):
        self.sign_in(self.teacher)
        stranger_id = self.theirs.records.first().id
        with patch('passport.narrative.complete',
                   return_value=f'Answer.\nRECORDS: {stranger_id}, 999999'):
            body = self.ask(self.mine).json()
        # Nothing valid was cited, so we report what was actually consulted.
        self.assertEqual(sorted(body['cited_record_ids']),
                         sorted(self.mine.records.exclude(
                             source=StudentRecord.QUESTION).values_list('id', flat=True)))

    def test_a_student_asking_never_sees_behavior_records(self):
        self.sign_in(self.mine.user)
        with patch('passport.narrative.complete', return_value='Answer.') as complete_mock:
            self.ask(self.mine)
        prompt = complete_mock.call_args.args[0]
        self.assertNotIn('Off task', prompt)
        self.assertNotIn('difficult week at home', prompt)

    def test_empty_question_is_rejected(self):
        self.sign_in(self.teacher)
        self.assertEqual(self.ask(self.mine, '   ').status_code, 400)
        self.assertEqual(StudentRecord.objects.filter(source=StudentRecord.QUESTION).count(), 0)


class DegradeTests(ApiTestCase):
    """No Bedrock key. Nothing 500s and nothing useless is cached."""

    def setUp(self):
        from .llm import LLMUnavailable
        patcher = patch('passport.narrative.complete', side_effect=LLMUnavailable('no key'))
        self.complete = patcher.start()
        self.addCleanup(patcher.stop)

    def test_passport_falls_back_to_the_records_and_is_not_cached(self):
        self.sign_in(self.teacher)
        body = self.client.get(f'/api/students/{self.mine.id}/passport/').json()
        self.assertEqual(self.client.get(
            f'/api/students/{self.mine.id}/passport/').status_code, 200)
        self.assertIn('not configured', body['sections']['overview']['teacher_voice'])
        self.assertTrue(body['sections']['performance'])
        self.assertEqual(Passport.objects.get(student=self.mine).sections, {})

    def test_ask_returns_200_and_says_ai_is_not_configured(self):
        self.sign_in(self.teacher)
        response = self.post(f'/api/students/{self.mine.id}/ask/', {'question': 'How is she?'})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn('AI is not configured', body['answer'])
        self.assertTrue(body['cited_record_ids'])
        self.assertEqual(StudentRecord.objects.filter(source=StudentRecord.QUESTION).count(), 1)

    def test_a_student_with_no_records_still_yields_a_passport(self):
        bare = make_student('Bare', 'Case')
        self.room.students.add(bare)
        self.sign_in(self.teacher)
        body = self.client.get(f'/api/students/{bare.id}/passport/').json()
        self.assertEqual(body['record_count'], 0)
        self.assertEqual(body['guardians'], [])
        self.assertEqual(body['student']['pronouns'], '')
        self.assertTrue(body['sections']['overview']['guardian_voice'])

        answer = self.post(f'/api/students/{bare.id}/ask/', {'question': 'Anything?'})
        self.assertEqual(answer.status_code, 200)


class InputTests(ApiTestCase):
    def test_guardian_writes_parent_input_and_a_student_writes_their_own(self):
        self.sign_in(self.guardian)
        body = self.post(f'/api/students/{self.mine.id}/input/', {
            'source': 'parent_input', 'title': 'From home', 'body': 'Mornings are hard.',
        })
        self.assertEqual(body.status_code, 201)
        self.assertEqual(body.json()['author'], 'One Guardian')
        self.assertEqual(body.json()['kind'], 'guardian note')

        self.client.logout()
        self.sign_in(self.mine.user)
        mine = self.post(f'/api/students/{self.mine.id}/input/', {
            'source': 'student_input', 'title': 'Me', 'body': 'I like the reading list early.',
        })
        self.assertEqual(mine.status_code, 201)
        self.assertEqual(mine.json()['source'], 'student_input')

    def test_a_role_cannot_write_someone_else_s_section(self):
        self.sign_in(self.guardian)
        wrong = self.post(f'/api/students/{self.mine.id}/input/', {
            'source': 'student_input', 'title': 'Not mine', 'body': 'x',
        })
        self.assertEqual(wrong.status_code, 403)

        self.client.logout()
        self.sign_in(self.teacher)
        teacher = self.post(f'/api/students/{self.mine.id}/input/', {
            'source': 'parent_input', 'title': 'Not mine', 'body': 'x',
        })
        self.assertEqual(teacher.status_code, 403)
        self.assertFalse(StudentRecord.objects.filter(
            source__in=['parent_input', 'student_input']).exists())

    def test_an_unknown_source_is_rejected(self):
        self.sign_in(self.guardian)
        response = self.post(f'/api/students/{self.mine.id}/input/', {
            'source': 'behavior', 'title': 'x', 'body': 'x',
        })
        self.assertEqual(response.status_code, 400)


class SessionTests(ApiTestCase):
    def test_login_sets_the_csrf_cookie_and_returns_the_session(self):
        response = self.post('/api/login/', {'username': 't.own', 'password': PASSWORD})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['role'], 'teacher')
        self.assertEqual([s['id'] for s in body['students']], [self.mine.id])
        self.assertEqual([c['name'] for c in body['classrooms']], ['Maths'])
        self.assertIn('csrftoken', response.cookies)
        self.assertTrue(body['csrf_token'])

    def test_a_browser_client_can_post_with_the_returned_csrf_token(self):
        """The exact flow the frontend must follow: log in, then send X-CSRFToken."""
        browser = Client(enforce_csrf_checks=True)
        token = browser.post(
            '/api/login/',
            {'username': 'g.one', 'password': PASSWORD},
            content_type='application/json',
        ).json()['csrf_token']

        body = {'source': 'parent_input', 'title': 'From home', 'body': 'Mornings are hard.'}
        self.assertEqual(
            browser.post(
                f'/api/students/{self.mine.id}/input/', body, content_type='application/json'
            ).status_code,
            403,
            'a POST without the header must be refused',
        )
        self.assertEqual(
            browser.post(
                f'/api/students/{self.mine.id}/input/', body,
                content_type='application/json', headers={'x-csrftoken': token},
            ).status_code,
            201,
        )

    def test_bad_credentials_are_401(self):
        response = self.post('/api/login/', {'username': 't.own', 'password': 'wrong'})
        self.assertEqual(response.status_code, 401)

    def test_logout_ends_the_session(self):
        self.sign_in(self.teacher)
        self.assertEqual(self.post('/api/logout/', {}).status_code, 200)
        self.assertIn(self.client.get('/api/me/').status_code, (401, 403))

    def test_the_spa_catch_all_still_works_around_the_api(self):
        self.assertEqual(self.client.get('/api/nope/').status_code, 404)
        # Any non-API path is the React app's to route.
        self.assertEqual(self.client.get('/students/1').resolver_match.url_name, 'spa')
