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
    StudentRecord.APP_INTEGRATION: 8,
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
    'Write it the way a colleague would say it out loud:\n'
    '- Lead with the thing that matters. First sentence is what the next adult '
    'most needs to know, not a recap of who the student is or what they are '
    'enrolled in.\n'
    '- Evidence carries the sentence; it is not the subject of it. Say "he is '
    'sharpest after lunch and flat first thing" and let one number back it. Never '
    'write a sentence whose content is a statistic, and never stack several.\n'
    '- Drop the instrumentation. No sample sizes, no "mean", no "across N '
    'samples", no parenthesised metrics. Round naturally: "about four in five", '
    '"most Mondays".\n'
    '- Name periods and subjects the way a person would — "fifth period", "in '
    'the lab" — not as a list of numbers.\n'
    '- Say less rather than padding. If a section has little to go on, two honest '
    'sentences beat five hedged ones.\n'
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


def ai_use_facts(records):
    """Lines summarising the latest cognitive-task-analysis record, if any.

    `records` is already filtered to `COGNITIVE_ANALYSIS`. The full structured
    analysis lives in `data`; only the rollup a teacher would actually scan is
    surfaced here, not the per-session or per-snippet detail.
    """
    if not records:
        return []
    latest = max(records, key=lambda r: r.date)
    data = latest.data if isinstance(latest.data, dict) else {}
    types = data.get('cognitive_types') or []
    evidence = data.get('evidence_base') or {}
    offloading = data.get('offloading') or {}
    lines = []

    sessions = evidence.get('session_count')
    if sessions:
        lines.append(
            f'AI-use analysis: {sessions} tutor sessions analysed '
            f'({evidence.get("sufficiency", "unrated")} evidence base).'
        )

    frequent = [t for t in types if t.get('presence_score', 0) >= 2
                and t.get('typical_depth_score', 0) >= 2]
    if frequent:
        named = ', '.join(t['label'] for t in frequent)
        lines.append(f'AI-use analysis, consistent strengths: {named}.')

    thin = [t for t in types if t.get('peak_depth_score', 0) == 0]
    if thin:
        named = ', '.join(t['label'] for t in thin)
        lines.append(f'AI-use analysis, never observed: {named}.')

    count = offloading.get('instance_count')
    if count:
        lines.append(f'AI-use analysis, offloading: {count} instances. {offloading.get("summary", "")}'.strip())

    return lines


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

    lines.extend(ai_use_facts(grouped.get(StudentRecord.COGNITIVE_ANALYSIS, [])))

    for source, label in (
        (StudentRecord.PARENT_INPUT, 'Guardian input'),
        (StudentRecord.STUDENT_INPUT, 'Student input'),
        (StudentRecord.OBSERVATION, 'Teacher observations'),
    ):
        lines.append(f'{label}: {len(grouped.get(source, []))} on file.')

    app_line = app_activity_facts(grouped.get(StudentRecord.APP_INTEGRATION, []))
    if app_line:
        lines.append(app_line)

    return lines


def app_activity_facts(app_records):
    """One overview line across a student's whole app history — not a single
    day. Gives the passport and ask/ a cheap sense that this source exists,
    the way every other source already gets one line here."""
    if not app_records:
        return None
    stats = app_topic_stats(app_records)
    attempted = sum(s['attempted'] for s in stats.values())
    if not attempted:
        return None
    correct = sum(s['correct'] for s in stats.values())
    weakest = min(
        (kv for kv in stats.items() if kv[1]['attempted'] >= MIN_ATTEMPTS_FOR_FLAG),
        key=lambda kv: kv[1]['accuracy'], default=None,
    )
    line = (
        f'App activity: {len(app_records)} sessions on file, '
        f'{correct / attempted:.0%} overall accuracy across {len(stats)} topics.'
    )
    if weakest:
        line += f' Weakest so far: {weakest[0]} at {weakest[1]["accuracy"]:.0%}.'
    return line


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
  "behavior": "...",
  "how_they_use_ai": "..."
}}

- overview.teacher_voice: 2-4 sentences. What a teacher who knows {name} would
  actually say to the next teacher over coffee. Start with what to expect from
  them, not with their enrolment.
- overview.guardian_voice: 1-3 sentences, from the guardian records only, in the
  spirit of what home has asked the school to understand. If there are none, say
  so in one sentence and stop.
- overview.student_voice: 1-3 sentences, from the student's own words and their
  tutor sessions. Prefer their phrasing over a summary of it. If they have
  written nothing, say so and stop.
- how_they_learn: 2-4 sentences on when and how the work goes well, and what to
  do with that. Concrete and usable — a reader should know what to change.
- performance: 2-4 sentences on the direction of travel. Which way each subject
  is going and roughly how far; a couple of real scores, not a table in prose.
- behavior: 2-4 sentences on what the behaviour and attendance records show and
  where they cluster. Adults only, so be direct without being clinical.
- how_they_use_ai: 2-4 sentences on the pattern in how {name} uses an AI tutor,
  grounded in the AI-use analysis record if one is on file: what kind of
  thinking actually shows up, where the work gets handed off instead, and one
  concrete thing a teacher could do about it. If there is no analysis on file,
  say so in one sentence and stop. Adults only, so be direct without being
  clinical — this may describe offloading a student would not want read back
  to them.

Every other section may be read by the student themselves, so keep them true but
supportive, and keep disciplinary detail out of them.
"""

VOICES = ('teacher_voice', 'guardian_voice', 'student_voice')
FLAT_SECTIONS = ('how_they_learn', 'performance', 'behavior', 'how_they_use_ai')


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
    ai_use = pick('ai-use analysis') or 'No AI-use analysis is on file for this student yet.'
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
        'how_they_use_ai': ai_use,
    }


# ---------------------------------------------------------------------------
# ask/
# ---------------------------------------------------------------------------

ASK_PROMPT = """{context}
{narrative}
QUESTION FROM A {role}: {question}

Answer in 2 to 5 sentences, for someone who has not read these records and is
reading between lessons. Answer the question asked, first sentence, before any
context. An answer that would fit any other student is wrong, so lean on the
specific dates, scores, periods and phrases — but weave them into normal
sentences rather than listing them, and skip sample sizes and averages. If the
records cannot answer the question, say exactly that and say what is missing.

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


def app_topic_stats(records):
    """{topic: {'attempted', 'correct', 'accuracy', 'avg_seconds'}} from a set
    of APP_INTEGRATION session records. Ignores sessions with no question
    breakdown — a session record is still valid without one."""
    totals = defaultdict(lambda: {'attempted': 0, 'correct': 0, 'seconds': 0})
    for record in records:
        data = record.data if isinstance(record.data, dict) else {}
        for question in data.get('questions') or []:
            if not isinstance(question, dict):
                continue
            topic = str(question.get('topic') or 'unspecified')
            row = totals[topic]
            row['attempted'] += 1
            row['correct'] += 1 if question.get('correct') else 0
            seconds = question.get('seconds')
            if isinstance(seconds, (int, float)) and not isinstance(seconds, bool):
                row['seconds'] += seconds

    stats = {}
    for topic, row in totals.items():
        n = row['attempted']
        stats[topic] = {
            'attempted': n,
            'correct': row['correct'],
            'accuracy': row['correct'] / n if n else 0.0,
            'avg_seconds': row['seconds'] / n if n else 0.0,
        }
    return stats


# A topic needs this many attempts before a flag means anything; three wrong
# out of three is noise, three wrong out of twelve is a pattern.
MIN_ATTEMPTS_FOR_FLAG = 4
ACCURACY_CONCERN = 0.5
ACCURACY_WATCH = 0.7
# Flagged when a topic takes this much longer than the student's own baseline
# for it — a personal comparison, not a fixed number of seconds.
PACE_RATIO_CONCERN = 1.8


def digest_flags(today_stats, baseline_stats):
    """Deterministic flags from computed accuracy and pace. Never left to the
    model to invent: a flag is either backed by a real threshold or it does
    not exist."""
    flags = []
    for topic, stats in sorted(today_stats.items()):
        if stats['attempted'] < MIN_ATTEMPTS_FOR_FLAG:
            continue
        if stats['accuracy'] < ACCURACY_CONCERN:
            flags.append({
                'topic': topic, 'kind': 'accuracy', 'severity': 'concern',
                'detail': f"{stats['correct']} of {stats['attempted']} correct today.",
            })
        elif stats['accuracy'] < ACCURACY_WATCH:
            flags.append({
                'topic': topic, 'kind': 'accuracy', 'severity': 'watch',
                'detail': f"{stats['correct']} of {stats['attempted']} correct today.",
            })

        base = baseline_stats.get(topic)
        if base and base['avg_seconds'] > 0 and stats['avg_seconds'] > 0:
            ratio = stats['avg_seconds'] / base['avg_seconds']
            if ratio >= PACE_RATIO_CONCERN:
                flags.append({
                    'topic': topic, 'kind': 'pace', 'severity': 'watch',
                    'detail': (
                        f"Taking about {ratio:.1f}x as long per question on this "
                        'topic as their own average.'
                    ),
                })
    return flags


# The one-day triage a teacher or guardian acts on. Computed from the flags,
# not left to the model: severity already carries the judgment, this just
# names the response it calls for.
ACTION_INTERVENE = 'intervene'
ACTION_CHECK_IN = 'check_in'
ACTION_CELEBRATE = 'celebrate'


def suggested_action(flags):
    severities = {f['severity'] for f in flags}
    if 'concern' in severities:
        return ACTION_INTERVENE
    if 'watch' in severities:
        return ACTION_CHECK_IN
    return ACTION_CELEBRATE


# A session's shape carries as much as its score. These thresholds decide
# only whether an observation is worth making at all — nothing here can move
# the triage, which stays on accuracy and pace.
MIN_QUESTIONS_FOR_SHAPE = 8
HALF_SPLIT_DELTA = 0.3
WRONG_STREAK = 3
PACE_GAP = 1.4


def session_shape(record):
    """Plain observations read out of one session's question sequence.

    Accuracy alone does not tell a teacher what to do. Four misses in a row is
    hitting a wall; four scattered through the set is carelessness. Wrong
    answers that came faster than the right ones is clicking through; wrong
    answers that took longer is genuine effort on something hard. Same score,
    three different conversations — and it is all already sitting in the
    per-question data the app partner sends.
    """
    data = record.data if isinstance(record.data, dict) else {}
    questions = [q for q in (data.get('questions') or []) if isinstance(q, dict)]
    if len(questions) < MIN_QUESTIONS_FOR_SHAPE:
        return []

    marks = [bool(q.get('correct')) for q in questions]
    topic = str(questions[0].get('topic') or 'this topic')
    out = []

    half = len(marks) // 2
    first, second = marks[:half], marks[half:]
    opened, closed = sum(first) / len(first), sum(second) / len(second)
    if opened - closed >= HALF_SPLIT_DELTA:
        out.append(
            f'{topic}: faded across the session — {sum(first)} of {len(first)} right to '
            f'start, {sum(second)} of {len(second)} after that.'
        )
    elif closed - opened >= HALF_SPLIT_DELTA:
        out.append(
            f'{topic}: warmed up — {sum(first)} of {len(first)} right to start, '
            f'{sum(second)} of {len(second)} after that.'
        )

    streak = longest = 0
    for mark in marks:
        streak = 0 if mark else streak + 1
        longest = max(longest, streak)
    if longest >= WRONG_STREAK:
        out.append(
            f'{topic}: missed {longest} in a row at the worst stretch, not scattered misses.'
        )

    def mean_seconds(want):
        values = [q['seconds'] for q, mark in zip(questions, marks)
                  if mark == want and isinstance(q.get('seconds'), (int, float))
                  and not isinstance(q.get('seconds'), bool)]
        return sum(values) / len(values) if values else None

    hit, miss = mean_seconds(True), mean_seconds(False)
    if hit and miss:
        if miss >= hit * PACE_GAP:
            out.append(
                f'{topic}: the misses took longer than the hits ({miss:.0f}s against '
                f'{hit:.0f}s) — worked at rather than rushed.'
            )
        elif hit >= miss * PACE_GAP:
            out.append(
                f'{topic}: the misses came faster than the hits ({miss:.0f}s against '
                f'{hit:.0f}s) — answered quickly rather than worked through.'
            )
    return out


def app_digest_facts(day_records, day, topic_stats, flags):
    lines = []
    sessions = sorted(day_records, key=lambda r: r.title)
    if not sessions:
        return ['No app activity on file for this date.']
    lines.append(
        f'{len(sessions)} session(s) on {day}: '
        + '; '.join(f'{r.title} ({int(_num(r, "duration_minutes") or 0)} min)' for r in sessions)
    )
    for topic, stats in sorted(topic_stats.items()):
        lines.append(
            f'Topic "{topic}": {stats["correct"]}/{stats["attempted"]} correct, '
            f'avg {stats["avg_seconds"]:.0f}s per question.'
        )
    lines += day_insights(sessions)
    if flags:
        lines.append('Computed flags: ' + '; '.join(
            f'{f["topic"]} ({f["kind"]}, {f["severity"]}): {f["detail"]}' for f in flags
        ))
    else:
        lines.append('No flags met the threshold today.')
    return lines


def day_insights(day_records):
    """Every session's shape for one day, in a stable order."""
    return [line for record in sorted(day_records, key=lambda r: r.title)
            for line in session_shape(record)]


DIGEST_PROMPT = """{context}

TODAY'S APP ACTIVITY ({date}):
{app_facts}

TODAY'S APP SESSION RECORDS:
{app_records}

The computed triage for today, from today's app performance alone, is: {action}
- intervene: at least one topic is a real concern — accuracy well below
  chance, or a topic taking far longer than this student's own pace.
- check_in: something is a little off and worth a quick look. Not urgent.
- celebrate: today's app work was solid or better.

Write a one-day digest for whoever checks in on {name} today. A teacher
reading this wants to know WHY the day looked this way, not just the score —
so use everything above, not only today's app numbers. If the wider record
(attendance, behaviour, engagement, a guardian or student note, a past
observation) offers a plausible reason for today's pattern, name it. If
nothing in the record explains it, say the day stands on its own; do not
invent a connection that is not supported above.

Reply with JSON only, no prose around it, using exactly these keys:

{{
  "action": "intervene" | "check_in" | "celebrate",
  "headline": "...",
  "narrative": "..."
}}

- action: must match the computed triage above exactly. Your job is to
  explain it, not re-decide it.
- headline: one sentence, the single most useful thing to know about today.
  Where a flag drove the triage, name that topic in it.
- narrative: 3-5 sentences, in two moves.
  First, WHAT: name the actual topics behind today's triage, the way a
  teacher would say them out loud — "stuck on adding fractions", "lost the
  thread on the inference questions" — never a bare score and never
  "one topic". Say HOW the work went, not only how much was right: the
  facts above tell you whether they faded or warmed up, whether the misses
  ran together or scattered, and whether the wrong answers were slower than
  the right ones (working at it) or faster (clicking through). That
  distinction is the most useful thing on the page, because it changes what
  the teacher should do — reteach the content, or sit with them while they
  do it. Use it whenever it is there. If the action is "celebrate", name
  what specifically went well with the same specificity.
  Then, WHY: a reason from the wider record above, if one is genuinely
  there — an absence, a behaviour entry, a flat period, something home or
  the student wrote, an older observation that shows the same thing. Say
  plainly that the day stands on its own if nothing in the record explains
  it. A cause you cannot point at a record for is an invention; so is a
  number or a flag that is not above.

This is read by an adult deciding whether {name} needs anything today, so be
direct. Skip sample sizes and jargon: "about half" not "50% (n=8)".
"""


def build_digest(student, all_records, day):
    """(summary, from_model). `all_records` is the student's whole record set,
    the same as the passport uses — the reason an app score dipped usually
    lives in a different source (attendance, a guardian note, engagement),
    not in the app data alone. The triage itself stays computed from app data
    only, so it never depends on what the model decides to notice.

    Nothing dated after `day` reaches the model. A digest for a past day is
    written from what was known that day, so the "why" can never be a record
    the student had not lived yet.
    """
    all_records = [r for r in all_records if r.date <= day]
    app_records = [r for r in all_records if r.source == StudentRecord.APP_INTEGRATION]
    day_records = [r for r in app_records if r.date == day]
    baseline_records = [r for r in app_records if r.date < day]

    topic_stats = app_topic_stats(day_records)
    baseline_stats = app_topic_stats(baseline_records)
    flags = digest_flags(topic_stats, baseline_stats)
    facts_lines = app_digest_facts(day_records, day, topic_stats, flags)
    # No app activity at all is itself worth a look, not a reason to praise.
    action = suggested_action(flags) if day_records else ACTION_CHECK_IN

    base = {
        'date': str(day),
        'action': action,
        'topics': [{'topic': t, **s} for t, s in sorted(topic_stats.items())],
        'flags': flags,
        # Computed the same way the flags are, and exposed for the same
        # reason: a client can show these verbatim without waiting on Claude.
        'insights': day_insights(day_records),
    }

    if not day_records:
        return {
            **base,
            'headline': f'No app activity on file for {student.first_name} on {day}.',
            'narrative': '',
        }, False

    try:
        reply = complete(
            DIGEST_PROMPT.format(
                context=context_block(student, all_records),
                name=student.first_name,
                date=day,
                action=action,
                app_facts='\n'.join(f'- {line}' for line in facts_lines),
                app_records='\n'.join(record_lines(day_records)),
            ),
            system=SYSTEM,
            max_tokens=700,
        )
        parsed = _json_object(reply)
        # `base['action']` is already the computed triage. The model was asked
        # to echo it so the prompt keeps it in view while writing, but its
        # copy is never read back — only `headline`/`narrative` are its own.
        return {
            **base,
            'headline': str(parsed.get('headline') or '').strip(),
            'narrative': str(parsed.get('narrative') or '').strip(),
        }, True
    except Exception as error:
        logger.warning('digest fell back to records: %s', error)
        return fallback_digest(student, base, facts_lines), False


def fallback_digest(student, base, facts_lines):
    preface = (
        'The AI narrative is not configured on this server, so this digest is '
        'assembled from the records themselves.'
    )
    concerning = [f for f in base['flags'] if f['severity'] == 'concern']
    watching = [f for f in base['flags'] if f['severity'] == 'watch']
    if concerning:
        headline = f"{concerning[0]['topic']}: {concerning[0]['detail']}"
    elif watching:
        headline = f"{watching[0]['topic']}: {watching[0]['detail']}"
    else:
        headline = f'No flags today for {student.first_name}.'
    return {**base, 'headline': headline, 'narrative': f'{preface} {" ".join(facts_lines)}'.strip()}


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
