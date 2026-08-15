"""Populate the demo database from the authored story arcs.

All data written here is synthetic.
"""

from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand

from passport.seed.arcs import DEMO_PASSWORD
from passport.seed.generate import run

# The story arcs carry every record except the AI-use analyses, which live in
# the repo as cognitive-task-analysis report folders. Both the "How they use
# AI" section and the roster's AI badge read `cognitive_analysis` records, so
# a database seeded without them looks correct everywhere else and silently
# drops those two — which is what the deployed demo did, since Railway's
# preDeployCommand runs this command and nothing else.
ANALYSIS_DIR = Path('cognitive-analysis-files/students')


class Command(BaseCommand):
    help = 'Seed the demo database with synthetic students built from story arcs.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset', action='store_true',
            help='Delete previously seeded users, classrooms and records first.',
        )
        parser.add_argument(
            '--quiet-logins', action='store_true',
            help='Skip the login table.',
        )

    def handle(self, *args, **options):
        summary = run(reset=options['reset'])

        self.stdout.write(self.style.SUCCESS(
            '{students} students ({heroes} story arcs), {teachers} teachers, '
            '{guardians} guardians, {classrooms} classrooms, {records} records'.format(**summary)
        ))

        if ANALYSIS_DIR.is_dir():
            call_command('import_cognitive_analysis', str(ANALYSIS_DIR))
        else:
            self.stdout.write(self.style.WARNING(
                f'{ANALYSIS_DIR} not found — seeded without AI-use analyses, so '
                'the "How they use AI" section and the roster AI badges will be empty.'
            ))

        if options['quiet_logins']:
            return

        rows = summary['logins']
        width = max(len(u) for u, _, _ in rows)
        self.stdout.write('')
        self.stdout.write(f'All accounts use the password: {DEMO_PASSWORD}')
        for role in ('teacher', 'student', 'guardian'):
            self.stdout.write('')
            self.stdout.write(self.style.MIGRATE_HEADING(f'{role}s'))
            for username, r, label in rows:
                if r == role:
                    self.stdout.write(f'  {username:<{width}}  {label}')
