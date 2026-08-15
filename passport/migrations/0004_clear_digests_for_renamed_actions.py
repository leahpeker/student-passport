"""The triage tiers were renamed: check_in -> watch, celebrate -> on_track.

Cached digests hold the old strings inside their `summary` JSON, and the
cache is returned wholesale, so a stale row would keep serving a tier name
the API no longer uses. These rows are a cache and nothing else — dropping
them costs one regeneration each and is simpler than rewriting JSON in place.
"""

from django.db import migrations


def clear_digests(apps, schema_editor):
    apps.get_model('passport', 'DailyDigest').objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('passport', '0003_alter_studentrecord_source_dailydigest'),
    ]

    # Reversing is a no-op: an empty cache is correct in either direction.
    operations = [
        migrations.RunPython(clear_digests, migrations.RunPython.noop),
    ]
