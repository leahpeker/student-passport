"""Checks that the seed actually contains the signals the demo claims.

Run with:  .venv/bin/python manage.py test passport.seed.test_seed
Or:        .venv/bin/python passport/seed/test_seed.py   (same thing, self-hosted)

Plain asserts on purpose. If one of these fails, the demo has lost its point.
"""

import os
import sys
from collections import Counter

if __name__ == '__main__':  # standalone: bootstrap Django before the app imports
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    import django

    django.setup()

from django.test import TransactionTestCase

from passport.models import Student, StudentRecord
from passport.seed import arcs
from passport.seed.generate import DAY_SET, run

SR = StudentRecord


def counts_by_student():
    return dict(
        Counter(StudentRecord.objects.values_list('student__user__username', flat=True))
    )


class SeedTests(TransactionTestCase):
    """One seed, then a re-seed, then assertions over the result."""

    def test_seed(self):
        first = run(reset=True)
        first_counts = counts_by_student()
        students_after_first = Student.objects.count()

        # 1. Running twice without --reset must not duplicate anything.
        second = run()
        assert Student.objects.count() == students_after_first, (
            f'reseed changed the student count: '
            f'{students_after_first} -> {Student.objects.count()}'
        )

        # 2. Same seed, identical record counts per student.
        assert counts_by_student() == first_counts, 'reseed produced different record counts'
        assert first['records'] == second['records'], (
            f'record totals differ between runs: {first["records"]} vs {second["records"]}'
        )

        # 3. Every hero spans at least six distinct sources.
        for key in first['hero_keys']:
            arc = next(a for a in arcs.ARCS if a['key'] == key)
            student = Student.objects.get(first_name=arc['first'], last_name=arc['last'])
            sources = set(student.records.values_list('source', flat=True))
            assert len(sources) >= 6, f'{key} only has sources {sorted(sources)}'
            assert SR.QUESTION not in sources, f'{key} should have no seeded question records'

        # 4. Every date is a weekday inside the school year.
        bad = [d for d in StudentRecord.objects.values_list('date', flat=True).distinct()
               if d not in DAY_SET]
        assert not bad, f'{len(bad)} record dates fall outside the school year or on a weekend'

        self.check_deshawn()
        self.check_maya()
        self.check_jordan()
        self.check_alina()
        self.check_sam()
        self.check_priya()

    # -- arc signals -------------------------------------------------------

    def check_deshawn(self):
        s = Student.objects.get(first_name='Deshawn', last_name='Carter')
        absences = list(s.records.filter(source=SR.ATTENDANCE, kind='absence')
                        .values_list('date', flat=True))
        assert absences, 'Deshawn has no absence records'
        by_weekday = Counter(d.weekday() for d in absences)
        school_days_by_weekday = Counter(d.weekday() for d in DAY_SET)
        rate = {wd: by_weekday.get(wd, 0) / school_days_by_weekday[wd] for wd in range(5)}
        others = max(rate[wd] for wd in range(1, 5))
        assert rate[0] > others * 2, (
            f'Monday absence rate {rate[0]:.3f} is not clearly above the rest {rate}'
        )

        # Behaviour flags sit in the period before lunch and vanish after it.
        periods = Counter(r.data['period'] for r in s.records.filter(source=SR.BEHAVIOR))
        before = periods[arcs.LUNCH_AFTER_PERIOD]
        after = sum(v for p, v in periods.items() if p > arcs.LUNCH_AFTER_PERIOD)
        assert before > 0.5 * sum(periods.values()), (
            f'pre-lunch period is not dominant in Deshawn behaviour: {dict(periods)}'
        )
        assert after <= 1, f'Deshawn has {after} post-lunch behaviour flags, expected ~0'

        # Afternoon engagement clearly beats morning engagement.
        morning, afternoon = [], []
        for r in s.records.filter(source=SR.ENGAGEMENT):
            (afternoon if r.data['period'] > arcs.LUNCH_AFTER_PERIOD else morning).append(
                r.data['rating'])
        assert sum(afternoon) / len(afternoon) > sum(morning) / len(morning) + 1.0, (
            'Deshawn afternoon engagement is not markedly higher than morning'
        )

    def check_maya(self):
        s = Student.objects.get(first_name='Maya', last_name='Okonkwo')
        hours = [r.data['hour'] for r in s.records.filter(source=SR.AI_TUTOR)]
        assert len(hours) >= 15, f'Maya has only {len(hours)} tutor sessions'
        late = [h for h in hours if h >= 23 or h <= 2]
        assert len(late) / len(hours) >= 0.7, (
            f'only {len(late)}/{len(hours)} of Maya\'s tutor sessions are after 11pm'
        )

        # Health-office visits sit the day before an assessment.
        assessment_dates = set(s.records.filter(source=SR.ASSESSMENT)
                               .values_list('date', flat=True))
        visits = list(s.records.filter(source=SR.SIS, kind='health_office')
                      .values_list('date', flat=True))
        assert visits, 'Maya has no health office records'
        eve = [d for d in visits
               if any((a - d).days in (1, 2, 3) for a in assessment_dates)]
        assert len(eve) >= 0.8 * len(visits), (
            f'only {len(eve)}/{len(visits)} of Maya\'s health visits precede an assessment'
        )

        # Scores stay top while engagement decays.
        scores = [r.data['percent'] for r in s.records.filter(source=SR.ASSESSMENT)]
        assert min(scores) >= 90, f'Maya has a non-top score: {sorted(scores)[:3]}'
        assert self._engagement_slope(s) < -0.5, 'Maya engagement does not decline over the year'

    def check_jordan(self):
        s = Student.objects.get(first_name='Jordan', last_name='Whitaker')
        by_format = {}
        for r in s.records.filter(source=SR.ASSESSMENT):
            by_format.setdefault(r.data['format'], []).append(r.data['percent'])
        project = sum(by_format['project']) / len(by_format['project'])
        timed = sum(by_format['timed_test']) / len(by_format['timed_test'])
        assert project - timed > 20, (
            f'Jordan project vs timed gap is only {project - timed:.1f} points'
        )

        hands_on = {6, 8}
        periods = Counter(r.data['period'] for r in s.records.filter(source=SR.BEHAVIOR))
        assert sum(periods[p] for p in hands_on) <= 1, (
            f'Jordan has behaviour flags in hands-on periods: {dict(periods)}'
        )

        # Engagement curve is the inverse of Maya's, period for period.
        maya = Student.objects.get(first_name='Maya', last_name='Okonkwo')
        shared = {1, 3, 4, 6, 8}
        jm = self._engagement_by_period(s)
        mm = self._engagement_by_period(maya)
        for p in shared:
            lecture = p in {1, 3, 4}
            assert (mm[p] > jm[p]) is lecture, (
                f'period {p}: Maya {mm[p]:.2f} vs Jordan {jm[p]:.2f} is not inverted'
            )

    def check_alina(self):
        s = Student.objects.get(first_name='Alina', last_name='Restrepo')
        reading = sorted(
            (r.date, r.data['percent'])
            for r in s.records.filter(source=SR.ASSESSMENT, data__subject='English')
        )
        assert reading[0][1] < 45 and reading[-1][1] > 75, (
            f'Alina reading does not climb steeply: {reading}'
        )
        math = [r.data['percent']
                for r in s.records.filter(source=SR.ASSESSMENT, data__subject='Mathematics')]
        assert min(math) >= 85, f'Alina math is not high from the start: {sorted(math)}'

        spanish = [r for r in s.records.filter(source=SR.AI_TUTOR)
                   if any(ch in r.body for ch in 'ñáéíóú¿')]
        assert len(spanish) >= 3, 'Alina has too few Spanish-language tutor sessions'

        by_period = self._engagement_by_period(s)
        assert min(by_period[2], by_period[6]) > max(by_period[3], by_period[4]) + 1.0, (
            f'Alina lab/studio engagement does not beat lecture: {by_period}'
        )

    def check_sam(self):
        s = Student.objects.get(first_name='Sam', last_name='Nakamura')
        move = next(r.date for r in s.records.filter(source=SR.SIS, kind='enrollment')
                    if 'Harborview' in r.title)
        engagement = list(s.records.filter(source=SR.ENGAGEMENT))
        assert all(r.date >= move for r in engagement), (
            'Sam has engagement samples from before he enrolled here'
        )
        ratings = [r.data['rating'] for r in engagement]
        assert sum(ratings) / len(ratings) < 3.0, 'Sam engagement is not low'

        scores = sorted((r.date, r.data['percent'])
                        for r in s.records.filter(source=SR.ASSESSMENT))
        before = [v for d, v in scores if d < move]
        dip = [v for d, v in scores if move <= d < move.replace(month=3, year=2026)]
        spring = [v for d, v in scores if d >= move.replace(month=3, year=2026)]
        assert sum(dip) / len(dip) < sum(before) / len(before) - 15, (
            'Sam scores do not drop after the move'
        )
        assert sum(spring) / len(spring) > sum(dip) / len(dip) + 5, (
            'Sam scores do not partly recover in spring'
        )

    def check_priya(self):
        s = Student.objects.get(first_name='Priya', last_name='Raghunathan')
        tests = [r.data['percent'] for r in s.records.filter(source=SR.ASSESSMENT,
                                                             kind='timed_test')]
        homework = [r.data['percent'] for r in s.records.filter(source=SR.ASSESSMENT,
                                                                kind='homework')]
        assert min(tests) >= 95, f'Priya tests are not near-perfect: {sorted(tests)}'
        assert max(homework) < 50, f'Priya homework completion is not low: {sorted(homework)}'

        by_period = self._engagement_by_period(s)
        best = max(by_period, key=lambda p: by_period[p])
        assert best == 8, f'Priya\'s standout period should be the elective, got {best}'
        rest = [v for p, v in by_period.items() if p != 8]
        assert by_period[8] > max(rest) + 1.5, (
            f'Priya is not clearly engaged only in the elective: {by_period}'
        )

    # -- helpers -----------------------------------------------------------

    @staticmethod
    def _engagement_by_period(student):
        buckets = {}
        for r in student.records.filter(source=SR.ENGAGEMENT):
            buckets.setdefault(r.data['period'], []).append(r.data['rating'])
        return {p: sum(v) / len(v) for p, v in buckets.items()}

    @staticmethod
    def _engagement_slope(student):
        """Mean rating in the last third of the year minus the first third."""
        rows = sorted((r.date, r.data['rating'])
                      for r in student.records.filter(source=SR.ENGAGEMENT))
        third = len(rows) // 3
        early = [v for _, v in rows[:third]]
        late = [v for _, v in rows[-third:]]
        return sum(late) / len(late) - sum(early) / len(early)


if __name__ == '__main__':
    from django.conf import settings
    from django.test.utils import get_runner

    sys.exit(bool(get_runner(settings)(verbosity=2).run_tests(['passport.seed.test_seed'])))
