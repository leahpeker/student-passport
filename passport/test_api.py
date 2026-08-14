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
