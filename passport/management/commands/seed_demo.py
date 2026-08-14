"""Populate the demo database from the authored story arcs.

All data written here is synthetic.
"""

from django.core.management.base import BaseCommand

from passport.seed.arcs import DEMO_PASSWORD
from passport.seed.generate import run


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
