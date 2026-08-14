"""Smallest thing that fails if the Bedrock wiring breaks."""

from django.conf import settings
from django.core.management.base import BaseCommand

from passport.llm import LLMUnavailable, complete


class Command(BaseCommand):
    help = 'Verify Claude on Bedrock is reachable and configured correctly.'

    def handle(self, *args, **options):
        self.stdout.write(f'region: {settings.BEDROCK_REGION}')
        self.stdout.write(f'model:  {settings.BEDROCK_MODEL}')
        try:
            answer = complete('Reply with exactly: ok', max_tokens=64)
        except LLMUnavailable as e:
            self.stdout.write(self.style.WARNING(f'not configured: {e}'))
            return
        assert answer.strip(), 'Bedrock returned an empty response'
        self.stdout.write(self.style.SUCCESS(f'bedrock ok -> {answer.strip()!r}'))
