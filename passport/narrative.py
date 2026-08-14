"""The written half of the passport: prompts, Claude, and the fallback.

Two callers — the passport endpoint (cached sections) and `ask/` (one
question). Both build the same grounded context: facts computed from the
records, then the records themselves. That is what makes an answer quote a
real date, score or period instead of sounding like any student.

Every helper here tolerates a missing record kind. A student with no
assessments, no guardian input or no engagement samples still yields every
section; the section is simply thinner.

Nothing calls Bedrock without a fallback. `LLMUnavailable` — or any other
failure from the model — degrades to text assembled from the records.

All records in this app are synthetic.
"""

import json
import logging
import re
from collections import Counter, defaultdict

from .llm import complete
from .models import StudentRecord

logger = logging.getLogger(__name__)

WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# Free text is the point of these; the high-volume numeric sources are
# summarised in `facts()` instead, so a low cap on them costs nothing.
PER_SOURCE_CAP = {
    StudentRecord.ENGAGEMENT: 12,
    StudentRecord.ATTENDANCE: 14,
    StudentRecord.ASSESSMENT: 20,
}
DEFAULT_CAP = 30
BODY_CHARS = 400

SYSTEM = (
    'You write the narrative of a Student Passport: one plain view of a single '
    'student, assembled from every school system that holds a piece of them. '
    'You are writing for the adult who meets this student next week.\n'
    'Rules:\n'
    '- Ground every sentence in the supplied records. Quote real dates, scores, '
    'periods, subjects and the words people actually wrote.\n'
    '- Never invent a record, a number, a diagnosis or a cause. If the records do '
    'not show something, say so plainly.\n'
    '- Describe the pattern, not a verdict. No labels, no medical or legal advice.\n'
    '- Plain English. Short sentences. No headings, no bullet lists, no markdown.\n'
    'The records are synthetic, written for a demonstration.'
)


# ---------------------------------------------------------------------------
# Facts computed from the records
# ---------------------------------------------------------------------------

def _num(record, key):
    """A numeric field out of the free-form `data` bag, or None."""
    data = record.data if isinstance(record.data, dict) else {}
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value


def _text(record, key):
    data = record.data if isinstance(record.data, dict) else {}
    value = data.get(key)
    return str(value) if isinstance(value, (str, int, float)) else None


def by_source(records):
    grouped = defaultdict(list)
    for record in records:
        grouped[record.source].append(record)
    return grouped


def engagement_by_period(records):
    """{period: (mean rating, sample count)}, empty when nothing is rated."""
    ratings = defaultdict(list)
    for record in records:
        period, rating = _num(record, 'period'), _num(record, 'rating')
        if period is not None and rating is not None:
            ratings[int(period)].append(rating)
    return {p: (sum(v) / len(v), len(v)) for p, v in sorted(ratings.items())}


def assessments_by_subject(records):
    """{subject: [(date, score), ...]} oldest first, so a trend is readable."""
    scores = defaultdict(list)
    for record in records:
        score = _num(record, 'percent')
        if score is None:
            score = _num(record, 'score')
        if score is None:
            continue
        scores[_text(record, 'subject') or 'Unspecified'].append((record.date, score))
    return {s: sorted(v) for s, v in sorted(scores.items())}


def absences_by_weekday(records):
    """Full-day absences per weekday name. Reads the kind, not a status flag."""
    counts = Counter()
    for record in records:
        if 'absen' in record.kind.lower() or _num(record, 'absent'):
            if 'summary' in record.kind.lower():
                continue
            counts[WEEKDAYS[record.date.weekday()]] += 1
    return counts


def facts(records):
    """Short factual lines. One source of truth for the prompt and the fallback."""
    grouped = by_source(records)
    lines = []

    if records:
        dates = [r.date for r in records]
        lines.append(
            f'{len(records)} records on file across {len(grouped)} sources, '
            f'{min(dates)} to {max(dates)}.'
        )

    engagement = engagement_by_period(grouped.get(StudentRecord.ENGAGEMENT, []))
    if engagement:
        detail = ', '.join(f'period {p} {m:.1f} (n={n})' for p, (m, n) in engagement.items())
        best = max(engagement.items(), key=lambda kv: kv[1][0])
        worst = min(engagement.items(), key=lambda kv: kv[1][0])
        lines.append(
            f'Engagement, mean rating out of 5 by period: {detail}. '
            f'Highest period {best[0]} at {best[1][0]:.1f}, '
            f'lowest period {worst[0]} at {worst[1][0]:.1f}.'
        )

    for subject, points in assessments_by_subject(grouped.get(StudentRecord.ASSESSMENT, [])).items():
        first, last = points[0], points[-1]
        lines.append(
            f'Assessment, {subject}: {len(points)} scores, '
            f'{first[1]:g} on {first[0]} to {last[1]:g} on {last[0]}.'
        )

    attendance = grouped.get(StudentRecord.ATTENDANCE, [])
    absences = absences_by_weekday(attendance)
    if absences:
        top, count = absences.most_common(1)[0]
        lines.append(
            f'Attendance: {sum(absences.values())} full-day absences, '
            f'most on {top} ({count} of them).'
        )
    tardies = [r for r in attendance if 'tard' in r.kind.lower()]
    if tardies:
        lines.append(f'Attendance: {len(tardies)} tardies logged.')
    rates = [_num(r, 'rate') for r in attendance]
    rates = [r for r in rates if r is not None]
    if rates:
        lines.append(f'Attendance rate across {len(rates)} months: {sum(rates) / len(rates):.0%}.')

    behavior = grouped.get(StudentRecord.BEHAVIOR, [])
    if behavior:
        periods = Counter(
            int(_num(r, 'period')) for r in behavior if _num(r, 'period') is not None
        )
        kinds = ', '.join(f'{k or "unlabelled"} {n}' for k, n in Counter(
            r.kind for r in behavior
        ).most_common())
        line = f'Behaviour: {len(behavior)} entries ({kinds}).'
        if periods:
            top, count = periods.most_common(1)[0]
            line += f' Largest cluster in period {top} with {count} of them.'
        lines.append(line)

    hours = [int(_num(r, 'hour')) for r in grouped.get(StudentRecord.AI_TUTOR, [])
             if _num(r, 'hour') is not None]
    if hours:
        late = sum(1 for h in hours if h >= 22 or h <= 4)
        lines.append(
            f'AI tutor: {len(hours)} sessions, {late} of them between 10pm and 4am.'
        )

    for source, label in (
        (StudentRecord.PARENT_INPUT, 'Guardian input'),
        (StudentRecord.STUDENT_INPUT, 'Student input'),
        (StudentRecord.OBSERVATION, 'Teacher observations'),
    ):
        lines.append(f'{label}: {len(grouped.get(source, []))} on file.')

    return lines


# ---------------------------------------------------------------------------
# The record dump
# ---------------------------------------------------------------------------

def record_lines(records):
    """One line per record, newest first, capped per source.

    The id prefix is what lets the model cite a record back to us.
    """
    seen = Counter()
    lines = []
    for record in sorted(records, key=lambda r: (r.date, r.id), reverse=True):
        cap = PER_SOURCE_CAP.get(record.source, DEFAULT_CAP)
        if seen[record.source] >= cap:
            continue
        seen[record.source] += 1
        body = ' '.join((record.body or '').split())[:BODY_CHARS]
        data = json.dumps(record.data, sort_keys=True, default=str) if record.data else ''
        author = f' (by {record.author.get_full_name()})' if record.author else ''
        lines.append(
            f'#{record.id} {record.date} [{record.source}/{record.kind or "note"}]'
            f'{author} {record.title}. {body} {data}'.rstrip()
        )
    return lines


def context_block(student, records):
    return '\n'.join([
        f'STUDENT: {student.name}, grade {student.grade}.',
        '',
        'FACTS COMPUTED FROM THE RECORDS:',
        *(f'- {line}' for line in facts(records)),
        '',
        f'RECORDS ({len(records)} on file, a capped sample follows):',
        *record_lines(records),
    ])


# ---------------------------------------------------------------------------
# Passport sections
# ---------------------------------------------------------------------------

SECTION_PROMPT = """{context}

Write the passport for {name}. Reply with JSON only, no prose around it, using
exactly these keys:

{{
  "overview": {{
    "teacher_voice": "...",
    "guardian_voice": "...",
    "student_voice": "..."
  }},
  "how_they_learn": "...",
  "performance": "...",
  "behavior": "..."
}}

- overview.teacher_voice: 3-5 sentences. What a teacher who knows {name} would
  tell the next teacher. Name the pattern the records show and the evidence for it.
- overview.guardian_voice: 2-4 sentences, written from the guardian records only.
  If there are none, say so in one sentence and stop.
- overview.student_voice: 2-4 sentences, from the student's own words and their
  tutor sessions. If they have written nothing, say so and stop.
- how_they_learn: 3-5 sentences on conditions, times of day and formats where the
  work goes well, with the periods and numbers that show it.
- performance: 3-5 sentences on the direction of travel per subject, with real
  scores and dates.
- behavior: 3-5 sentences on what the behaviour and attendance records show,
  including when and where entries cluster. This section is read by adults only.

Every other section may be read by the student themselves, so keep them true but
supportive, and keep disciplinary detail out of them.
"""

VOICES = ('teacher_voice', 'guardian_voice', 'student_voice')
FLAT_SECTIONS = ('how_they_learn', 'performance', 'behavior')


def _json_object(text):
    """The first JSON object in a reply, tolerating fences and stray prose."""
    start, end = text.find('{'), text.rfind('}')
    if start < 0 or end <= start:
        raise ValueError('no JSON object in reply')
    return json.loads(text[start:end + 1])


def _shape(raw):
    overview = raw.get('overview') or {}
    sections = {'overview': {v: str(overview.get(v) or '').strip() for v in VOICES}}
    for key in FLAT_SECTIONS:
        sections[key] = str(raw.get(key) or '').strip()
    if not any(sections['overview'].values()):
        raise ValueError('reply had no overview text')
    return sections


def build_sections(student, records):
    """(sections, from_model). Falls back to the records when Claude is out."""
    try:
        reply = complete(
            SECTION_PROMPT.format(context=context_block(student, records), name=student.first_name),
            system=SYSTEM,
            max_tokens=3000,
        )
        return _shape(_json_object(reply)), True
    except Exception as error:  # LLMUnavailable, Bedrock errors, bad JSON
        logger.warning('passport narrative fell back to records: %s', error)
        return fallback_sections(student, records), False


def _latest_body(grouped, source, empty):
    entries = sorted(grouped.get(source, []), key=lambda r: r.date, reverse=True)
    if not entries:
        return empty
    latest = entries[0]
    return f'From {latest.date}: "{latest.body or latest.title}"'


def fallback_sections(student, records):
    """Sections assembled from the records alone. No model involved."""
    grouped = by_source(records)
    computed = facts(records)
    name = student.first_name
    preface = (
        'The AI narrative is not configured on this server, so this section is '
        'assembled from the records themselves.'
    )

    def pick(*needles):
        return ' '.join(l for l in computed if any(n in l.lower() for n in needles))

    engagement = pick('engagement') or 'No engagement samples are on file.'
    scores = pick('assessment,') or 'No scored assessments are on file.'
    conduct = pick('behaviour', 'attendance') or 'No behaviour or attendance entries are on file.'
    observations = [
        f'{r.date}: {r.title}' for r in
        sorted(grouped.get(StudentRecord.OBSERVATION, []), key=lambda r: r.date, reverse=True)[:3]
    ]

    return {
        'overview': {
            'teacher_voice': f'{preface} {" ".join(computed[:2])}'.strip(),
            'guardian_voice': _latest_body(
                grouped, StudentRecord.PARENT_INPUT,
                'No guardian input is on file for this student yet.',
            ),
            'student_voice': _latest_body(
                grouped, StudentRecord.STUDENT_INPUT,
                f'{name} has not written anything into the passport yet.',
            ),
        },
        'how_they_learn': ' '.join(filter(None, [
            engagement,
            'Most recent teacher observations: ' + '; '.join(observations) + '.'
            if observations else '',
        ])),
        'performance': scores,
        'behavior': conduct,
    }


# ---------------------------------------------------------------------------
# ask/
# ---------------------------------------------------------------------------

ASK_PROMPT = """{context}
{narrative}
QUESTION FROM A {role}: {question}

Answer in 3 to 6 sentences, for someone who has not read these records. Quote
the specific dates, scores, periods and phrases you relied on — an answer that
would fit any other student is wrong. If the records cannot answer the question,
say exactly that and say what is missing.

End with one final line in exactly this form, listing the record ids you used:
RECORDS: 12, 45, 88
"""

CITATION = re.compile(r'^[ \t]*RECORDS[ \t]*:[ \t]*(.*)$', re.MULTILINE | re.IGNORECASE)


def _split_citations(text, valid_ids):
    match = CITATION.search(text)
    if not match:
        return text.strip(), []
    cited = [int(n) for n in re.findall(r'\d+', match.group(1))]
    answer = (text[:match.start()] + text[match.end():]).strip()
    return answer, [i for i in cited if i in valid_ids]


def answer_question(student, question, records, sections=None, role='teacher'):
    """(answer, cited_record_ids, from_model).

    `cited_record_ids` is what the model said it used, filtered to ids we
    actually supplied. When it cites nothing usable we return every record put
    in front of it, which is still a real count of what was consulted.
    """
    consulted = [r.id for r in records]
    narrative = ''
    if sections:
        narrative = '\nPASSPORT NARRATIVE ALREADY ON FILE:\n' + json.dumps(sections, indent=1)
    prompt = ASK_PROMPT.format(
        context=context_block(student, records),
        narrative=narrative,
        role=role.upper(),
        question=question,
    )
    try:
        reply = complete(prompt, system=SYSTEM, max_tokens=1200)
    except Exception as error:
        logger.warning('ask/ fell back to records: %s', error)
        return fallback_answer(student, question, records), consulted, False

    answer, cited = _split_citations(reply, set(consulted))
    if not answer:
        return fallback_answer(student, question, records), consulted, False
    return answer, cited or consulted, True


def fallback_answer(student, question, records):
    """No model available. Say so, then answer with what the records show."""
    computed = facts(records)
    if not computed:
        return (
            'AI is not configured on this server, and there are no records on file '
            f'for {student.first_name} to answer from.'
        )
    return (
        'AI is not configured on this server, so this is not an answer to the '
        f'question — it is what {student.first_name}\'s {len(records)} records show. '
        + ' '.join(computed)
    )
