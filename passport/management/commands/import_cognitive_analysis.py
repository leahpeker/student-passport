"""Import cognitive-task-analysis reports as `cognitive_analysis` records.

Reads a directory of `<student-key>/{analysis.json,report.md}` folders, as
produced by the cognitive-task-analysis skill, and writes one
`StudentRecord` per student: `data` carries the full analysis.json (what the
"How they use AI" passport section and its chart are built from), `body`
carries the report's snapshot paragraph.

Students are matched by first name, case-insensitively, against the
subdirectory name — true for the six seeded story-arc students this was
built for. Re-running updates the existing record rather than duplicating it.

All data imported here is synthetic.
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from passport.models import Student, StudentRecord


def snapshot_paragraph(report_md):
    """The paragraph under '## Snapshot' in the report, or ''."""
    lines = report_md.splitlines()
    if '## Snapshot' not in lines:
        return ''
    para = []
    for line in lines[lines.index('## Snapshot') + 1:]:
        if line.startswith('#'):
            break
        if line.strip():
            para.append(line.strip())
        elif para:
            break
    return ' '.join(para)


class Command(BaseCommand):
    help = 'Import cognitive-task-analysis report folders as cognitive_analysis records.'

    def add_arguments(self, parser):
        parser.add_argument(
            'directory', nargs='?', default='cognitive-analysis-files/students',
            help='Directory with one subdirectory per student, each holding '
                 'analysis.json and report.md.',
        )

    def handle(self, *args, **options):
        root = Path(options['directory'])
        if not root.is_dir():
            raise CommandError(f'{root} is not a directory')

        found = False
        for student_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            analysis_path = student_dir / 'analysis.json'
            if not analysis_path.exists():
                continue
            found = True

            student = Student.objects.filter(first_name__iexact=student_dir.name).first()
            if student is None:
                self.stdout.write(self.style.WARNING(
                    f'{student_dir.name}: no student with that first name, skipped'
                ))
                continue

            analysis = json.loads(analysis_path.read_text())
            report_path = student_dir / 'report.md'
            snapshot = snapshot_paragraph(report_path.read_text()) if report_path.exists() else ''
            sessions = analysis.get('evidence_base', {}).get('session_count', 0)

            _, created = StudentRecord.objects.update_or_create(
                student=student, source=StudentRecord.COGNITIVE_ANALYSIS,
                kind='ai_use_analysis',
                defaults={
                    'date': analysis['generated_at'][:10],
                    'title': f'AI-use cognitive analysis ({sessions} sessions)',
                    'body': snapshot,
                    'data': analysis,
                },
            )
            verb = 'created' if created else 'updated'
            self.stdout.write(self.style.SUCCESS(f'{student.name}: {verb}'))

        if not found:
            self.stdout.write(self.style.WARNING(f'No analysis.json found under {root}.'))
