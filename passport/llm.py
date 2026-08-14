"""Claude, via Amazon Bedrock.

Auth is a Bedrock API key in AWS_BEARER_TOKEN_BEDROCK, which the SDK sends as a
bearer token. Note it cannot be combined with AWS profile credentials — if both
are present the client raises, so the key replaces them.
"""

import os

from anthropic import AnthropicBedrock
from django.conf import settings


class LLMUnavailable(RuntimeError):
    """No Bedrock key configured. Callers degrade instead of failing."""


def client():
    # AWS_BEARER_TOKEN_BEDROCK is the name botocore/the SDK look for;
    # BEDROCK_API_KEY is accepted as an alias.
    key = os.getenv('AWS_BEARER_TOKEN_BEDROCK') or os.getenv('BEDROCK_API_KEY')
    if not key:
        raise LLMUnavailable('set AWS_BEARER_TOKEN_BEDROCK (or BEDROCK_API_KEY)')
    # Passed explicitly so a stray AWS_PROFILE in the environment can't collide.
    return AnthropicBedrock(aws_region=settings.BEDROCK_REGION, api_key=key)


def complete(prompt, system=None, max_tokens=8000):
    """One-shot completion. Returns the response text."""
    kwargs = {
        'model': settings.BEDROCK_MODEL,
        'max_tokens': max_tokens,
        'messages': [{'role': 'user', 'content': prompt}],
    }
    if system:
        kwargs['system'] = system
    response = client().messages.create(**kwargs)
    return ''.join(b.text for b in response.content if b.type == 'text')
