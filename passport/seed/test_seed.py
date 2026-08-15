"""Checks that the seed actually contains the signals the demo claims.

Run with:  .venv/bin/python manage.py test passport.seed.test_seed
Or:        .venv/bin/python passport/seed/test_seed.py   (same thing, self-hosted)

Plain asserts on purpose. If one of these fails, the demo has lost its point.
"""

import os
import sys
import re
from collections import Counter
from datetime import date

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

        self.check_pronouns()
        self.check_enrolment_window()
        self.check_named_teachers()
        self.check_no_hand_written_counts()
        self.check_cited_attendance()
        self.check_app_integration()

        self.check_deshawn()
        self.check_maya()
        self.check_jordan()
        self.check_alina()
        self.check_sam()
        self.check_priya()

    # -- cross-arc consistency ---------------------------------------------

    def check_pronouns(self):
        """Every student carries pronouns, and a hero's are the ones the arc authored."""
        authored = {(a['first'], a['last']): a['pronouns'] for a in arcs.ARCS}
        for s in Student.objects.all():
            found = {r.data['pronouns'] for r in s.records.filter(source=SR.SIS)
                     if 'pronouns' in (r.data or {})}
            assert len(found) == 1, (
                f'{s.first_name} {s.last_name} has pronouns {found or "nowhere"} in the SIS '
                f'record; the file header renders blank without exactly one'
            )
            want = authored.get((s.first_name, s.last_name))
            assert want is None or found == {want}, (
                f'{s.first_name} {s.last_name} seeded as {found}, arc says {want}'
            )

    def check_enrolment_window(self):
        """Nothing this school wrote may predate the day the student arrived.

        The arrival date is read back out of the seeded rows, not out of the arc
        dict, so dropping the arc's `start` key trips this too. A transferred
        student's file legitimately holds earlier records — the transfer file —
        but those carry no author here and no attendance, behaviour or
        engagement row of ours.
        """
        ours = {SR.ATTENDANCE, SR.BEHAVIOR, SR.ENGAGEMENT, SR.APP_INTEGRATION}
        checked = 0
        for s in Student.objects.all():
            arrivals = [r.date for r in s.records.filter(source=SR.SIS, kind='enrollment')
                        if arcs.SCHOOL_NAME in r.title]
            if not arrivals:
                continue
            checked += 1
            start = max(arrivals)
            early = [(r.source, r.kind, r.date.isoformat()) for r in s.records.all()
                     if r.date < start and (r.source in ours or r.author_id is not None)]
            assert not early, (
                f'{s.first_name} {s.last_name} enrolled here {start} but has {len(early)} '
                f'of this school\'s records before that: {early[:6]}'
            )
        assert checked, 'no transferred student in the seed; this check tested nothing'

    def check_named_teachers(self):
        """A teacher an observation names must actually have records for the student.

        Covers both the author (a note about a student they never see) and any
        colleague the note points at (a claim about someone else's referrals).
        """
        by_key = {t['key']: t['last'] for t in arcs.TEACHERS}
        for arc in arcs.ARCS:
            s = Student.objects.get(first_name=arc['first'], last_name=arc['last'])
            authored = Counter(
                r.author.last_name
                for r in s.records.filter(author__isnull=False).select_related('author')
            )
            firsthand = Counter(
                r.author.last_name
                for r in s.records.filter(author__isnull=False,
                                          source__in=[SR.OBSERVATION, SR.BEHAVIOR])
                .select_related('author')
            )
            for e in arc.get('observations', []):
                writer = by_key[e['teacher']]
                assert authored[writer] > 1, (
                    f'{arc["key"]}: {writer} wrote an observation on {e["date"]} but has '
                    f'no other record for this student'
                )
                for last in by_key.values():
                    if last == writer or last not in e['body']:
                        continue
                    assert firsthand[last] > 0, (
                        f'{arc["key"]}: the {e["date"]} observation talks about {last}, who '
                        f'has written nothing about this student'
                    )

    def check_no_hand_written_counts(self):
        """Authored prose must not assert a tally the stochastic rows decide.

        "Three referrals" or "nine times" in a hand-written note is a claim the
        generator has no reason to honour. Say "more than once", or leave a
        `{...}` placeholder and let `cite_attendance` fill in the real number.
        """
        num = (r'(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d+)')
        patterns = [
            # "three referrals", "14 absences"
            re.compile(rf'\b{num}\s+(?:referrals?|write[-\s]ups?|absences?|tardies)\b', re.I),
            # "written them up nine times"
            re.compile(rf'\b(?:wrote|writes|written|logged|flagged|referred)\b'
                       rf'[^.]{{0,60}}\b{num}\s+times\b', re.I),
            # "the third time I have written a note like this"
            re.compile(r'\b(?:second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\s+'
                       r'(?:time|referral|note|write[-\s]up)\b', re.I),
        ]
        offenders = []
        for arc in arcs.ARCS:
            for field in ('observations', 'documents', 'parent_input', 'student_input'):
                for e in arc.get(field, []):
                    for pattern in patterns:
                        hit = pattern.search(e['body'])
                        if hit:
                            offenders.append(
                                f'{arc["key"]}/{field} {e["date"]}: "{hit.group(0)}"')
        assert not offenders, (
            'authored prose asserts counts the generator does not produce:\n  '
            + '\n  '.join(offenders)
        )

    def check_cited_attendance(self):
        """Where a document cites absence and tardy counts, they are the real ones."""
        seen = 0
        for arc in arcs.ARCS:
            s = Student.objects.get(first_name=arc['first'], last_name=arc['last'])
            for e in arc.get('documents', []):
                if '{absences}' not in e['body']:
                    continue
                seen += 1
                upto = date.fromisoformat(e['date'])
                real = Counter(
                    s.records.filter(source=SR.ATTENDANCE, date__lte=upto)
                    .values_list('kind', flat=True))
                body = s.records.get(source=SR.DOCUMENT, date=upto, title=e['title']).body
                assert e['body'].format(absences=real['absence'],
                                        tardies=real['tardy']) == body, (
                    f'{arc["key"]} document on {e["date"]} cites counts the rows do not '
                    f'support (absences {real["absence"]}, tardies {real["tardy"]}): {body}'
                )
        assert seen, 'no document cites attendance counts; the substitution path is untested'

    def check_app_integration(self):
        """App-integration sessions exist, have a sane question shape, and the
        accuracy they carry actually correlates with the same per-period
        baseline that drives engagement — the two sources should agree, since
        one is derived from the other."""
        sessions = list(StudentRecord.objects.filter(source=SR.APP_INTEGRATION))
        assert sessions, 'no app_integration records were seeded at all'

        for record in sessions:
            questions = record.data.get('questions')
            assert questions, f'{record.id} has no question breakdown'
            for q in questions:
                assert isinstance(q['correct'], bool), f'{record.id}: correct is not a bool'
                assert q['seconds'] > 0, f'{record.id}: non-positive seconds'
                assert q['topic'], f'{record.id}: blank topic'

        # A hero's strongest engagement period should score higher in the app
        # than their weakest — same rng-independent signal both sources share.
        checked = 0
        for arc in arcs.ARCS:
            base = arc['engagement']['base']
            if len(base) < 2:
                continue
            s = Student.objects.get(first_name=arc['first'], last_name=arc['last'])
            best_period = max(base, key=base.get)
            worst_period = min(base, key=base.get)
            # Sessions carry a subject, not a period; map back through the
            # classroom that period belongs to.
            by_period = {c['period']: c['subject'] for c in arcs.CLASSROOMS}
            best_subject = by_period.get(best_period)
            worst_subject = by_period.get(worst_period)
            if not best_subject or not worst_subject or best_subject == worst_subject:
                continue

            def accuracy_for(subject):
                qs = [q for r in s.records.filter(source=SR.APP_INTEGRATION, data__subject=subject)
                      for q in r.data['questions']]
                return sum(1 for q in qs if q['correct']) / len(qs) if qs else None

            best_acc, worst_acc = accuracy_for(best_subject), accuracy_for(worst_subject)
            if best_acc is None or worst_acc is None:
                continue
            checked += 1
            assert best_acc >= worst_acc, (
                f'{arc["key"]}: app accuracy in their best period ({best_subject}, '
                f'{best_acc:.2f}) is not >= their worst ({worst_subject}, {worst_acc:.2f})'
            )
        assert checked, 'no arc had both a best- and worst-period subject to compare'

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

        # The cadence should read as a life, not as a generator: the gap varies
        # and no single weekday owns the pattern.
        gaps = {min((a - d).days for a in assessment_dates if (a - d).days > 0)
                for d in visits}
        assert len(gaps) > 1, f'every health visit sits the same distance from a test: {gaps}'
        weekdays = Counter(d.weekday() for d in visits)
        assert max(weekdays.values()) <= 0.6 * len(visits), (
            f'Maya\'s health visits are locked to one weekday: {dict(weekdays)}'
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
