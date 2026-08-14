"""Authored seed content. Data only — no database access, no logic.

Everything here is invented for the demo. The point of authoring it by hand
is that each arc emits *correlated* evidence across several sources, so the
underlying cause is inferable from the whole picture and is never stated in
any single record.

Date rule: every date below is a weekday inside the school year. The
generator re-checks that and raises if an authored date ever drifts.
"""

from datetime import date

SCHOOL_YEAR_START = date(2025, 9, 2)
SCHOOL_YEAR_END = date(2026, 6, 5)

DEMO_PASSWORD = 'demo12345'
SCHOOL_NAME = 'Harborview High School'

# Bell schedule. Lunch sits between period 4 and period 5, which is what
# makes "the period right before lunch" a real position in the day.
PERIOD_TIMES = {
    1: '08:00',
    2: '08:55',
    3: '09:50',
    4: '10:45',
    5: '12:20',
    6: '13:15',
    7: '14:10',
    8: '15:05',
}
LUNCH_AFTER_PERIOD = 4

TEACHERS = [
    {'key': 'ramirez', 'first': 'Elena', 'last': 'Ramirez'},
    {'key': 'chen', 'first': 'Wei', 'last': 'Chen'},
    {'key': 'boyd', 'first': 'Marcus', 'last': 'Boyd'},
    {'key': 'okafor', 'first': 'Nkechi', 'last': 'Okafor'},
]

# mode drives the engagement and behaviour language, and is the axis Jordan's
# arc swings on.
CLASSROOMS = [
    {'code': 'alg2', 'name': 'Algebra II', 'subject': 'Mathematics',
     'grade': '10', 'period': 1, 'teacher': 'ramirez', 'mode': 'lecture'},
    {'code': 'bio', 'name': 'Biology', 'subject': 'Science',
     'grade': '9', 'period': 2, 'teacher': 'chen', 'mode': 'lab'},
    {'code': 'lit', 'name': 'World Literature', 'subject': 'English',
     'grade': '', 'period': 3, 'teacher': 'boyd', 'mode': 'lecture'},
    {'code': 'hist', 'name': 'U.S. History', 'subject': 'Social Studies',
     'grade': '', 'period': 4, 'teacher': 'boyd', 'mode': 'lecture'},
    {'code': 'geo', 'name': 'Geometry', 'subject': 'Mathematics',
     'grade': '9', 'period': 5, 'teacher': 'ramirez', 'mode': 'practice'},
    {'code': 'art', 'name': 'Studio Art', 'subject': 'Visual Arts',
     'grade': '', 'period': 6, 'teacher': 'okafor', 'mode': 'studio'},
    {'code': 'phys', 'name': 'Physics', 'subject': 'Science',
     'grade': '11', 'period': 7, 'teacher': 'chen', 'mode': 'lab'},
    {'code': 'cs', 'name': 'Intro to Computer Science', 'subject': 'Computer Science',
     'grade': '', 'period': 8, 'teacher': 'okafor', 'mode': 'project'},
]

# Engagement note pools, keyed by (mode, band). Band is 'low' (1-2),
# 'mid' (3) or 'high' (4-5). Kept generic so the arc-specific colour comes
# from the authored records, not from a thousand hand-written samples.
ENGAGEMENT_NOTES = {
    ('lecture', 'low'): [
        'Spot check at minute 20: head down, notebook closed.',
        'Eyes on the clock through the direct-instruction block.',
        'Did not write anything during the fifteen-minute lecture segment.',
    ],
    ('lecture', 'mid'): [
        'Took notes, did not volunteer.',
        'Followed along, answered when called on.',
    ],
    ('lecture', 'high'): [
        'Hand up three times during the discussion.',
        'Annotated the reading unprompted and pushed back on the framing.',
    ],
    ('lab', 'low'): [
        'Let the partner run the whole protocol.',
        'Stayed at the bench but did not touch the equipment.',
    ],
    ('lab', 'mid'): [
        'Split the procedure with a partner and recorded results.',
        'Worked steadily through the station.',
    ],
    ('lab', 'high'): [
        'Ran the station, then re-ran it to check an outlier.',
        'Still at the bench when the bell rang.',
    ],
    ('practice', 'low'): [
        'Two of twelve problems attempted by the end of the period.',
        'Packet unstarted at the halfway check.',
    ],
    ('practice', 'mid'): [
        'Worked the set at pace with one prompt.',
        'Finished the assigned problems, skipped the extension.',
    ],
    ('practice', 'high'): [
        'Finished the set early and started the extension without being asked.',
        'Explained the shortcut to the table.',
    ],
    ('studio', 'low'): [
        'Sat with the materials out, produced nothing.',
        'Cleaned up twenty minutes early.',
    ],
    ('studio', 'mid'): [
        'Made steady progress on the current piece.',
        'Worked without prompting for most of the period.',
    ],
    ('studio', 'high'): [
        'Worked through the passing bell.',
        'Reworked the piece a third time and asked to stay through lunch.',
    ],
    ('project', 'low'): [
        'Repository untouched for the period.',
        'Watched the pair-programming partner type.',
    ],
    ('project', 'mid'): [
        'Committed the assigned function and stopped there.',
        'Kept pace with the sprint board.',
    ],
    ('project', 'high'): [
        'Shipped the assignment, then refactored it for fun.',
        'Stayed after to debug something outside the spec.',
    ],
}


# ---------------------------------------------------------------------------
# Hero arcs
# ---------------------------------------------------------------------------
#
# Each arc dict may carry:
#   key, first, last, pronouns, grade, dob, seed, classrooms, guardians
#   engagement: {'base': {period: float}, 'trend': float, 'jitter': float,
#                'per_week': int, 'start': iso|None}
#   absences:   {'count': int, 'weights': weightspec, 'tardies': int,
#                'tardy_weights': weightspec}
#   behavior:   {'count': int, 'period_weights': {p: w}, 'weights': weightspec,
#                'bodies': [...], 'kind': str, 'severity': int}
#   assessments/sis/documents/observations/ai_tutor/parent_input/
#   student_input: authored lists of records
#   ai_tutor_fill: {'count', 'hour_weights', 'bodies', 'weights'}
#
# A weightspec multiplies optional tables: 'weekday' (0=Mon), 'month',
# 'from_day_of_month' (day, multiplier), 'window' [(start, end, multiplier)].

ARCS = [
    # -----------------------------------------------------------------
    # 1. Maya Okonkwo — high achiever masking anxiety.
    # Signals: scores stay at the top all year while engagement decays;
    # tutor sessions migrate to 11pm-2am and shift from content to
    # sufficiency; health-office visits land the day before every
    # assessment; one observation of crying before a test she then aced.
    # -----------------------------------------------------------------
    {
        'key': 'maya',
        'first': 'Maya', 'last': 'Okonkwo', 'pronouns': 'she/her',
        'grade': '10', 'dob': '2010-03-14', 'seed': 1001,
        'classrooms': ['alg2', 'lit', 'hist', 'art', 'cs'],
        'guardians': [
            {'first': 'Ngozi', 'last': 'Okonkwo', 'relationship': 'mother'},
            {'first': 'Daniel', 'last': 'Okonkwo', 'relationship': 'father'},
        ],
        'engagement': {
            'base': {1: 4.7, 3: 4.6, 4: 4.4, 6: 3.6, 8: 4.1},
            'trend': -1.6, 'jitter': 0.35, 'per_week': 3,
        },
        'absences': {'count': 3, 'tardies': 2},
        'behavior': {
            'count': 3, 'kind': 'minor', 'severity': 1,
            'period_weights': {4: 3.0, 3: 1.0, 1: 1.0},
            'bodies': [
                'Left the room without permission during test review. Found in the health office.',
                'Asked to redo an assignment that had already been graded 98. Told her no; she asked again after class.',
                'Would not hand in the draft at the bell. Kept editing until asked twice.',
            ],
        },
        'assessments': [
            {'date': '2025-09-19', 'subject': 'Mathematics', 'kind': 'Unit 1 test',
             'format': 'timed_test', 'score': 97,
             'body': 'Finished first. Every step shown, twice in places.'},
            {'date': '2025-10-17', 'subject': 'English', 'kind': 'Analytical essay',
             'format': 'project', 'score': 96,
             'body': 'Third submitted draft. The first two were already passing.'},
            {'date': '2025-11-14', 'subject': 'Social Studies', 'kind': 'Unit 3 exam',
             'format': 'timed_test', 'score': 95,
             'body': 'Highest in the section. Asked afterward which question she lost the point on.'},
            {'date': '2025-12-12', 'subject': 'Mathematics', 'kind': 'Semester exam',
             'format': 'timed_test', 'score': 98, 'body': 'No errors.'},
            {'date': '2026-01-30', 'subject': 'Computer Science', 'kind': 'Project checkpoint',
             'format': 'project', 'score': 94,
             'body': 'Complete and working. She described it as "the worst thing I have turned in".'},
            {'date': '2026-02-27', 'subject': 'English', 'kind': 'Comparative essay',
             'format': 'project', 'score': 97, 'body': 'Argument is a year ahead of the rubric.'},
            {'date': '2026-03-27', 'subject': 'Mathematics', 'kind': 'Unit 6 test',
             'format': 'timed_test', 'score': 96, 'body': 'Left ten minutes of the period unused, checking.'},
            {'date': '2026-04-24', 'subject': 'Social Studies', 'kind': 'Document-based question',
             'format': 'timed_test', 'score': 97, 'body': 'Cited six of the seven documents.'},
            {'date': '2026-05-22', 'subject': 'Mathematics', 'kind': 'Final exam',
             'format': 'timed_test', 'score': 97, 'body': 'Consistent with every other assessment this year.'},
        ],
        'sis': [
            {'date': '2025-09-02', 'kind': 'enrollment', 'title': 'Enrolled, grade 10',
             'body': 'Continuing student. Schedule: periods 1, 3, 4, 6, 8. Honors track in mathematics and English.'},
            {'date': '2025-09-18', 'kind': 'health_office', 'title': 'Health office visit',
             'body': 'Reported stomach ache during period 3. Rested 25 minutes. No fever. Returned to class.',
             'data': {'minutes_out': 25, 'period': 3}},
            {'date': '2025-10-16', 'kind': 'health_office', 'title': 'Health office visit',
             'body': 'Headache. Water and 20 minutes in the quiet room. Declined a call home.',
             'data': {'minutes_out': 20, 'period': 4}},
            {'date': '2025-11-13', 'kind': 'health_office', 'title': 'Health office visit',
             'body': 'Nausea, no fever, no other symptoms. Asked whether she could stay through the period.',
             'data': {'minutes_out': 35, 'period': 3}},
            {'date': '2025-12-11', 'kind': 'health_office', 'title': 'Health office visit',
             'body': 'Stomach ache again. Vitals normal. Third visit this term, all on a Thursday.',
             'data': {'minutes_out': 30, 'period': 4}},
            {'date': '2026-01-29', 'kind': 'health_office', 'title': 'Health office visit',
             'body': 'Reported feeling shaky and cold. Warm, no fever. Rested and returned.',
             'data': {'minutes_out': 25, 'period': 3}},
            {'date': '2026-02-26', 'kind': 'health_office', 'title': 'Health office visit',
             'body': 'Stomach ache. Asked twice whether the visit would be recorded anywhere teachers could see.',
             'data': {'minutes_out': 20, 'period': 4}},
            {'date': '2026-03-26', 'kind': 'health_office', 'title': 'Health office visit',
             'body': 'Headache and light sensitivity. Reported four hours of sleep.',
             'data': {'minutes_out': 40, 'period': 3}},
            {'date': '2026-04-23', 'kind': 'health_office', 'title': 'Health office visit',
             'body': 'Nausea. Vitals normal. Returned to class before the bell on her own.',
             'data': {'minutes_out': 20, 'period': 4}},
            {'date': '2026-05-21', 'kind': 'health_office', 'title': 'Health office visit',
             'body': 'Stomach ache. Ninth visit this year. No pattern of illness in the record.',
             'data': {'minutes_out': 25, 'period': 3}},
        ],
        'documents': [
            {'date': '2026-01-16', 'kind': 'report_card', 'title': 'Semester 1 report card',
             'body': 'Algebra II A. World Literature A. U.S. History A. Studio Art B+. '
                     'Computer Science A. Teacher comment (Ramirez): "Maya is the strongest '
                     'mathematician in the section and the least willing to believe it."'},
            {'date': '2026-03-06', 'kind': 'counseling_note', 'title': 'Counseling check-in summary',
             'body': 'Student-requested drop-in, 15 minutes. Wanted to discuss whether a B+ in '
                     'Studio Art would appear on a transcript. Declined a follow-up appointment. '
                     'Said everything else is fine.'},
        ],
        'observations': [
            {'date': '2025-11-14', 'teacher': 'boyd', 'title': 'Before the unit exam',
             'body': 'Came in fifteen minutes before the bell and was crying at her desk. Would not '
                     'say why, asked me not to tell anyone, then asked whether she could see the '
                     'grading rubric one more time. She sat the exam and scored the highest in the '
                     'section. She asked on the way out which one she got wrong.'},
            {'date': '2026-02-10', 'teacher': 'ramirez', 'title': 'Third period, after returning work',
             'body': 'Handed back a 96. She looked at it for a long time and then asked if she could '
                     'do the corrections anyway. Everyone else was packing up.'},
            {'date': '2026-04-30', 'teacher': 'okafor', 'title': 'Studio, end of unit',
             'body': 'She is careful in studio in a way that costs her. Will not start a piece until '
                     'she is sure how it ends. Today she erased a good drawing twice.'},
        ],
        'ai_tutor': [
            {'date': '2025-09-18', 'hour': 22, 'minute': 40,
             'body': 'Can you check my proof for problem 14? I think step three is wrong.'},
            {'date': '2025-10-16', 'hour': 23, 'minute': 12,
             'body': 'Is this thesis statement strong enough or does it read like I did it fast?'},
            {'date': '2025-11-13', 'hour': 23, 'minute': 48,
             'body': 'I have gone through the study guide four times. What else should I be doing.'},
            {'date': '2025-12-11', 'hour': 0, 'minute': 55,
             'body': 'If I got a 95 on this exam what would that do to my average.'},
            {'date': '2026-01-29', 'hour': 1, 'minute': 20,
             'body': 'Can you tell from my essay whether it sounds like I tried hard enough?'},
            {'date': '2026-02-26', 'hour': 1, 'minute': 47,
             'body': 'Is a 94 bad. Be honest.'},
            {'date': '2026-03-26', 'hour': 2, 'minute': 5,
             'body': 'How do people know when their work is good enough to stop.'},
            {'date': '2026-04-23', 'hour': 0, 'minute': 38,
             'body': 'I already finished this. Can you give me harder versions of the same problems '
                     'so I know I actually understand it and did not just memorise it.'},
            {'date': '2026-05-21', 'hour': 1, 'minute': 12,
             'body': 'What happens to someone who was good at school and then stops being good at it.'},
        ],
        'ai_tutor_fill': {
            'count': 16,
            'hour_weights': {21: 0.6, 22: 1.5, 23: 4.0, 0: 3.5, 1: 3.0, 2: 1.5},
            'bodies': [
                'Can you re-explain the chain rule from the start, I want to be sure.',
                'Is my outline missing anything the rubric asks for?',
                'Give me five more practice problems on this, harder than the homework.',
                'Did I use this term correctly or does it sound wrong.',
                'How long should this assignment have taken someone.',
                'Can you grade this the way a strict teacher would.',
                'Check my working again please, I do not trust it.',
                'What would a perfect answer to this look like.',
            ],
        },
        'parent_input': [
            {'date': '2025-11-20', 'author': 0, 'title': 'Note from home',
             'body': 'Her light is still on when I leave for work at five in the morning. She says '
                     'it is homework. She has never once asked us for help with homework.'},
            {'date': '2026-03-13', 'author': 1, 'title': 'Note from home',
             'body': 'She would not come to her cousin\'s birthday because of a project that was '
                     'already finished. She showed it to me. It was finished.'},
        ],
        'student_input': [
            {'date': '2025-10-03', 'title': 'What I want you to know',
             'body': 'I am fine. Please do not make this a thing.'},
            {'date': '2026-04-17', 'title': 'What I want you to know',
             'body': 'I do not really like any of these classes. I just do not want to be the person '
                     'who used to be good at this.'},
        ],
    },

    # -----------------------------------------------------------------
    # 2. Deshawn Carter — food insecurity at home.
    # Signals: absences pile onto Mondays and onto the last week of the
    # month; behaviour flags sit almost entirely in period 4 (the period
    # before lunch) and vanish after it; engagement is much higher in
    # afternoon periods; a guardian note about moving to nights; strong
    # scores whenever he is in the room. Nothing names the cause.
    # -----------------------------------------------------------------
    {
        'key': 'deshawn',
        'first': 'Deshawn', 'last': 'Carter', 'pronouns': 'he/him',
        'grade': '9', 'dob': '2011-06-22', 'seed': 1002,
        'classrooms': ['bio', 'lit', 'hist', 'geo', 'art'],
        'guardians': [
            {'first': 'Tanisha', 'last': 'Carter', 'relationship': 'mother',
             'also_guardian_of': ['nia_carter']},
        ],
        'engagement': {
            'base': {2: 2.5, 3: 2.6, 4: 2.0, 5: 4.4, 6: 4.5},
            'trend': 0.2, 'jitter': 0.4, 'per_week': 3,
        },
        'absences': {
            'count': 24,
            'weights': {'weekday': {0: 7.0}, 'from_day_of_month': (24, 2.5)},
            'tardies': 9,
            'tardy_weights': {'weekday': {0: 4.0, 1: 1.5}},
        },
        'behavior': {
            'count': 17, 'kind': 'minor', 'severity': 1,
            'period_weights': {4: 10.0, 3: 2.0, 2: 1.2, 5: 0.15, 6: 0.1},
            'weights': {'from_day_of_month': (24, 2.0), 'weekday': {0: 1.8}},
            'bodies': [
                'Short with a classmate over a borrowed pencil. Apologised at the bell without being asked.',
                'Head down for the last twenty minutes. Would not start the exit ticket.',
                'Asked to leave for the water fountain three times in one period.',
                'Snapped when a table partner reached across him. Calm again by the next period.',
                'Put his hood up and stopped responding around 11:20.',
                'Argued about the length of the reading, then did it.',
                'Asked how long until the bell four times.',
                'Left his seat to look out the door twice in ten minutes.',
            ],
        },
        'assessments': [
            {'date': '2025-09-25', 'subject': 'Science', 'kind': 'Cell unit quiz',
             'format': 'timed_test', 'score': 88, 'body': 'Strong on the diagram section.'},
            {'date': '2025-10-23', 'subject': 'Mathematics', 'kind': 'Geometry unit 2 test',
             'format': 'timed_test', 'score': 91, 'body': 'Second highest in fifth period.'},
            {'date': '2025-11-06', 'subject': 'Mathematics', 'kind': 'Geometry unit 3 test (make-up)',
             'format': 'timed_test', 'score': 89,
             'body': 'Absent on the test day. Sat it during lunch the following Thursday and still '
                     'finished with time left.'},
            {'date': '2025-12-04', 'subject': 'English', 'kind': 'Narrative writing task',
             'format': 'project', 'score': 84, 'body': 'Late by two days, complete when it arrived.'},
            {'date': '2026-01-22', 'subject': 'Science', 'kind': 'Semester exam',
             'format': 'timed_test', 'score': 87, 'body': 'No sign of the absences in the content knowledge.'},
            {'date': '2026-02-19', 'subject': 'Mathematics', 'kind': 'Geometry unit 5 test (make-up)',
             'format': 'timed_test', 'score': 92,
             'body': 'Missed Monday. Sat this at lunch on Thursday. Highest score in the section.'},
            {'date': '2026-03-19', 'subject': 'Social Studies', 'kind': 'Unit 6 exam',
             'format': 'timed_test', 'score': 79, 'body': 'Lower than his usual. Fourth period, end of March.'},
            {'date': '2026-04-16', 'subject': 'Science', 'kind': 'Lab practical',
             'format': 'project', 'score': 93, 'body': 'Ran the whole protocol without the sheet.'},
            {'date': '2026-05-14', 'subject': 'Mathematics', 'kind': 'Final exam',
             'format': 'timed_test', 'score': 90, 'body': 'Consistent with the year when he is here.'},
        ],
        'sis': [
            {'date': '2025-09-02', 'kind': 'enrollment', 'title': 'Enrolled, grade 9',
             'body': 'Schedule: periods 2, 3, 4, 5, 6. Household includes one sibling enrolled in '
                     'grade 11 at this school.'},
            {'date': '2025-10-14', 'kind': 'household_update', 'title': 'Household record updated',
             'body': 'Address unchanged. Primary daytime contact changed from mother to grandmother. '
                     'Meal benefit application received 10/14, held pending income documentation. '
                     'Transport: walks, no bus assignment.'},
            {'date': '2026-01-13', 'kind': 'household_update', 'title': 'Household record updated',
             'body': 'Emergency contact order changed: grandmother first, mother second. Note from '
                     'the front office that calls before 2pm go unanswered.'},
        ],
        'documents': [
            {'date': '2026-01-16', 'kind': 'report_card', 'title': 'Semester 1 report card',
             'body': 'Biology A-. World Literature B. U.S. History C+. Geometry A. Studio Art A-. '
                     'Attendance: 14 absences, 6 tardies. Teacher comment (Ramirez): "Attendance is '
                     'the only thing between Deshawn and the honor roll. In fifth period he is one '
                     'of the two strongest students I have."'},
        ],
        'observations': [
            {'date': '2025-11-19', 'teacher': 'boyd', 'title': 'Fourth period, again',
             'body': 'Fourth period is where I lose him. Today he asked twice how long until the bell '
                     'and put his head down at 11:20. I have him in third as well and third is fine. '
                     'Ms. Ramirez says he is a different student in fifth.'},
            {'date': '2026-01-27', 'teacher': 'ramirez', 'title': 'Fifth period',
             'body': 'He came in first, before the bell, and had the warm-up done before I finished '
                     'taking roll. He asked for the extension problems. This is the same student who '
                     'has three referrals from the period before lunch.'},
            {'date': '2026-03-24', 'teacher': 'okafor', 'title': 'Sixth period, end of March',
             'body': 'Quiet and slow to start this week, which is not like him for a Tuesday. Picked '
                     'up after about twenty minutes. This is the third time I have written a note '
                     'like this in the last week of a month.'},
        ],
        'ai_tutor': [
            {'date': '2025-10-06', 'hour': 6, 'minute': 42,
             'body': 'can you explain again the thing about angles from friday, i missed it'},
            {'date': '2025-11-03', 'hour': 6, 'minute': 51,
             'body': 'what did geometry cover today, im not going to be there'},
            {'date': '2026-01-05', 'hour': 6, 'minute': 38,
             'body': 'i have to catch up on two days of history, whats the fastest way'},
            {'date': '2026-02-23', 'hour': 6, 'minute': 45,
             'body': 'is there a way to do the make up test online instead of at lunch'},
            {'date': '2026-04-13', 'hour': 15, 'minute': 40,
             'body': 'can you check my proof, im in the library until they close'},
        ],
        'ai_tutor_fill': {
            'count': 14,
            'hour_weights': {6: 2.5, 7: 1.0, 15: 4.0, 16: 3.5, 17: 2.0},
            'bodies': [
                'walk me through this proof one more time',
                'whats the difference between these two theorems',
                'i missed monday, what do i need to know',
                'can you quiz me on the vocab for tomorrow',
                'how do i show the work for this one',
                'is my answer right or did i round wrong',
            ],
        },
        'parent_input': [
            {'date': '2025-10-21', 'author': 0, 'title': 'Note from home',
             'body': 'I moved to the overnight shift at the distribution centre in October, it pays '
                     'better. I am home around seven in the morning and I sleep until two. Deshawn '
                     'gets himself and his sister out the door. Mondays are the hardest, the weekend '
                     'throws the whole thing off.'},
            {'date': '2026-02-11', 'author': 0, 'title': 'Note from home',
             'body': 'We stopped doing breakfast at the house, nobody is up for it. He says he eats '
                     'at school so I let it go. Please stop sending the trip money slips home, I '
                     'already told the office we would sort it out.'},
        ],
        'student_input': [
            {'date': '2025-12-09', 'title': 'What I want you to know',
             'body': 'Fifth period is my favourite. Ms. Ramirez does not ask me why I am tired.'},
            {'date': '2026-05-05', 'title': 'What I want you to know',
             'body': 'Fourth period is the longest hour of the day and I do not know why. By fifth I '
                     'am fine. I am not trying to be rude to Mr. Boyd.'},
        ],
    },

    # -----------------------------------------------------------------
    # 3. Alina Restrepo — newcomer, English learner, strong in math.
    # Signals: reading scores start low and climb steeply while math is
    # high from day one; tutor questions switch between Spanish and
    # English; engagement peaks in lab, studio and partner work and
    # bottoms out in lecture; an observation of her translating.
    # -----------------------------------------------------------------
    {
        'key': 'alina',
        'first': 'Alina', 'last': 'Restrepo', 'pronouns': 'she/her',
        'grade': '9', 'dob': '2011-01-30', 'seed': 1003,
        'classrooms': ['bio', 'lit', 'hist', 'geo', 'art'],
        'guardians': [
            {'first': 'Marisol', 'last': 'Restrepo', 'relationship': 'mother'},
            {'first': 'Hernán', 'last': 'Restrepo', 'relationship': 'father'},
        ],
        'engagement': {
            'base': {2: 4.6, 3: 2.3, 4: 2.0, 5: 4.3, 6: 4.6},
            'trend': 0.5, 'jitter': 0.35, 'per_week': 3,
        },
        'absences': {'count': 5, 'tardies': 6,
                     'tardy_weights': {'month': {9: 5.0, 10: 2.0}}},
        'behavior': {
            'count': 4, 'kind': 'minor', 'severity': 1,
            'period_weights': {5: 2.0, 2: 1.5, 6: 1.0},
            'bodies': [
                'Out of her seat without permission. She was at another table explaining the instructions.',
                'Talking during independent work. Both students were on task in two languages.',
                'Handed her calculator to a classmate mid-quiz. Reminded of the rule.',
                'Stayed at the bench past the bell to finish a partner\'s write-up.',
            ],
        },
        'assessments': [
            {'date': '2025-09-11', 'subject': 'English', 'kind': 'Reading benchmark (fall)',
             'format': 'timed_test', 'score': 38,
             'body': 'Comprehension well below grade level. She answered the inference items she '
                     'reached; she ran out of time at question 19 of 40.'},
            {'date': '2025-09-12', 'subject': 'Mathematics', 'kind': 'Math placement screener',
             'format': 'timed_test', 'score': 88,
             'body': 'Placed above the grade 9 sequence on the numeric reasoning strand.'},
            {'date': '2025-10-10', 'subject': 'English', 'kind': 'Reading progress check',
             'format': 'timed_test', 'score': 47, 'body': 'Reached question 27 this time.'},
            {'date': '2025-10-23', 'subject': 'Mathematics', 'kind': 'Geometry unit 2 test',
             'format': 'timed_test', 'score': 91,
             'body': 'Full marks on the working. Lost points only where the question was a word problem.'},
            {'date': '2025-11-21', 'subject': 'English', 'kind': 'Reading progress check',
             'format': 'timed_test', 'score': 55, 'body': 'Finished the section for the first time.'},
            {'date': '2025-12-05', 'subject': 'English', 'kind': 'English proficiency screener',
             'format': 'timed_test', 'score': 52,
             'body': 'Speaking is the lowest of the four domains. Reading has moved two bands since September.'},
            {'date': '2026-01-23', 'subject': 'English', 'kind': 'Reading progress check',
             'format': 'timed_test', 'score': 64, 'body': 'Steepest jump of any student in the cohort.'},
            {'date': '2026-01-27', 'subject': 'Mathematics', 'kind': 'Geometry semester exam',
             'format': 'timed_test', 'score': 94, 'body': 'Top of the section.'},
            {'date': '2026-03-13', 'subject': 'English', 'kind': 'Reading progress check',
             'format': 'timed_test', 'score': 73, 'body': 'Within four points of the grade-level band.'},
            {'date': '2026-04-10', 'subject': 'Science', 'kind': 'Lab practical',
             'format': 'project', 'score': 95,
             'body': 'Ran the protocol and wrote the discussion in English without a translation tool.'},
            {'date': '2026-05-15', 'subject': 'English', 'kind': 'Reading benchmark (spring)',
             'format': 'timed_test', 'score': 79,
             'body': 'Forty-one points above where she started in September.'},
            {'date': '2026-05-20', 'subject': 'Mathematics', 'kind': 'Geometry final exam',
             'format': 'timed_test', 'score': 96, 'body': 'High all year, from the first week.'},
        ],
        'sis': [
            {'date': '2025-09-02', 'kind': 'enrollment', 'title': 'Enrolled, grade 9',
             'body': 'New to the district. Prior school: Institución Educativa San José, Medellín, '
                     'Colombia. Entry date to a school in this country: 2025-08-25. Home language: '
                     'Spanish. Schedule: periods 2, 3, 4, 5, 6.'},
            {'date': '2025-09-16', 'kind': 'program_flag', 'title': 'English learner services',
             'body': 'Identified for English language development services following the home '
                     'language survey and initial screener. Designated support scheduled during '
                     'advisory, not during a content period.'},
        ],
        'documents': [
            {'date': '2025-09-30', 'kind': 'el_plan', 'title': 'English learner services plan',
             'body': 'Goals: academic vocabulary in content classes; extended time on reading '
                     'assessments; bilingual glossary permitted in mathematics and science. '
                     'Note from the ELD teacher: "Her mathematics is well ahead of her English. Do '
                     'not read a low reading score as a low ceiling."'},
            {'date': '2026-01-16', 'kind': 'report_card', 'title': 'Semester 1 report card',
             'body': 'Biology B+. World Literature C. U.S. History C-. Geometry A. Studio Art A. '
                     'Teacher comment (Chen): "Her lab write-ups are better science than most of the '
                     'ones written in a first language."'},
        ],
        'observations': [
            {'date': '2025-11-18', 'teacher': 'ramirez', 'title': 'Fifth period',
             'body': 'She finished the problem set with fifteen minutes left and spent the rest of '
                     'the period translating the instructions for a new student at her table. In both '
                     'directions. Then she checked his work and made him redo two.'},
            {'date': '2026-02-04', 'teacher': 'boyd', 'title': 'Third period',
             'body': 'She has not spoken aloud in my class since September. Her written responses are '
                     'getting stronger every month. Today I asked her a question directly and she '
                     'wrote the answer on paper and slid it across.'},
            {'date': '2026-04-22', 'teacher': 'chen', 'title': 'Second period lab',
             'body': 'She corrected my unit conversion in front of the class. She was right. She said '
                     'it in English.'},
        ],
        'ai_tutor': [
            {'date': '2025-09-15', 'hour': 17, 'minute': 20,
             'body': '¿Cómo se dice "denominador" en inglés? Y "mínimo común múltiplo".'},
            {'date': '2025-10-07', 'hour': 18, 'minute': 5,
             'body': 'Entiendo el problema pero no entiendo la pregunta. ¿Me la puedes explicar más simple?'},
            {'date': '2025-11-12', 'hour': 17, 'minute': 48,
             'body': 'Necesito explicar mi respuesta en inglés. ¿Puedes revisar esta oración?'},
            {'date': '2026-01-14', 'hour': 18, 'minute': 30,
             'body': 'What is the English word for the top number in a fraction? I know it in Spanish.'},
            {'date': '2026-03-04', 'hour': 17, 'minute': 15,
             'body': 'Is this sentence correct English? "The cell divide in two identical parts."'},
            {'date': '2026-05-06', 'hour': 18, 'minute': 12,
             'body': 'I want to say this in class tomorrow without reading it. Can you help me practise it?'},
        ],
        'ai_tutor_fill': {
            'count': 12,
            'hour_weights': {16: 2.0, 17: 4.0, 18: 4.0, 19: 2.0},
            'bodies': [
                '¿Puedes revisar mi párrafo por favor?',
                'What does "infer" mean in a test question?',
                'Explícame este problema en español y después en inglés.',
                'Is my grammar right here? I am not sure about the verb.',
                '¿Cómo se dice esto de una manera más formal?',
                'Give me the vocabulary for the biology test in both languages.',
            ],
        },
        'parent_input': [
            {'date': '2025-10-09', 'author': 0, 'title': 'Nota de casa / Note from home',
             'body': 'Llegamos en agosto. En Medellín ella iba un año adelantada en matemáticas. Le '
                     'da pena hablar en clase porque teme equivocarse en inglés, no porque no sepa '
                     'la respuesta. / We arrived in August. In Medellín she was a year ahead in '
                     'mathematics. She is embarrassed to speak in class because she is afraid of '
                     'making a mistake in English, not because she does not know the answer.'},
            {'date': '2026-04-08', 'author': 1, 'title': 'Note from home',
             'body': 'She reads the news in English at the kitchen table now and asks me words. In '
                     'September she would not read anything in English at home at all.'},
        ],
        'student_input': [
            {'date': '2026-02-18', 'title': 'What I want you to know',
             'body': 'In math I know the answer before I know how to say it. In history I know '
                     'nothing until I have read it three times, and then I know it.'},
        ],
    },

    # -----------------------------------------------------------------
    # 4. Jordan Whitaker — 504 plan for ADHD, hands-on learner.
    # Signals: referrals concentrate in the long lecture blocks and are
    # near zero in studio and project periods; the engagement curve is
    # the mirror image of Maya's; scores swing forty points on assessment
    # format alone; a 504 plan document explains the accommodations
    # without explaining the pattern.
    # -----------------------------------------------------------------
    {
        'key': 'jordan',
        'first': 'Jordan', 'last': 'Whitaker', 'pronouns': 'they/them',
        'grade': '10', 'dob': '2010-08-09', 'seed': 1004,
        'classrooms': ['alg2', 'lit', 'hist', 'art', 'cs'],
        'guardians': [
            {'first': 'Rebecca', 'last': 'Whitaker', 'relationship': 'mother'},
        ],
        'engagement': {
            'base': {1: 2.4, 3: 2.1, 4: 1.9, 6: 4.8, 8: 4.7},
            'trend': 0.3, 'jitter': 0.4, 'per_week': 3,
        },
        'absences': {'count': 6, 'tardies': 14,
                     'tardy_weights': {'weekday': {0: 2.0}}},
        'behavior': {
            'count': 19, 'kind': 'referral', 'severity': 2,
            'period_weights': {4: 6.0, 3: 4.0, 1: 3.0, 6: 0.1, 8: 0.1},
            'bodies': [
                'Out of seat four times during the thirty-minute direct-instruction block.',
                'Drumming on the desk. Stopped when asked, restarted within a minute.',
                'Answered a question three topics ahead of where we were, then lost the thread entirely.',
                'Talking to a neighbour through the lecture. The talk was about the material.',
                'Asked to go to the bathroom at minute twelve, back at minute thirty.',
                'Took apart a pen during the reading and could not say what the reading was about.',
                'Called out five times without raising a hand.',
                'Turned around to face the back of the room and stayed that way.',
            ],
        },
        'assessments': [
            {'date': '2025-09-19', 'subject': 'Mathematics', 'kind': 'Unit 1 test',
             'format': 'timed_test', 'score': 61,
             'body': 'Left the last two pages blank. Every attempted item was correct.'},
            {'date': '2025-10-09', 'subject': 'Computer Science', 'kind': 'Build project',
             'format': 'project', 'score': 96,
             'body': 'Delivered more than the spec asked for and demonstrated it to the class.'},
            {'date': '2025-10-31', 'subject': 'English', 'kind': 'Timed in-class essay',
             'format': 'timed_test', 'score': 58,
             'body': 'One strong paragraph and then nothing. The clock was on the board.'},
            {'date': '2025-11-20', 'subject': 'Visual Arts', 'kind': 'Portfolio review',
             'format': 'project', 'score': 94, 'body': 'Six finished pieces, two beyond the brief.'},
            {'date': '2025-12-12', 'subject': 'Mathematics', 'kind': 'Semester exam',
             'format': 'timed_test', 'score': 64, 'body': 'Ran out of time again, same pattern.'},
            {'date': '2026-01-29', 'subject': 'Social Studies', 'kind': 'Research project',
             'format': 'project', 'score': 92,
             'body': 'Built a physical timeline. Content is at or above the honors level.'},
            {'date': '2026-02-27', 'subject': 'English', 'kind': 'Timed reading assessment',
             'format': 'timed_test', 'score': 66, 'body': 'Same student, same subject, thirty points down.'},
            {'date': '2026-03-26', 'subject': 'Computer Science', 'kind': 'Capstone milestone',
             'format': 'project', 'score': 98, 'body': 'Best project in the section.'},
            {'date': '2026-04-24', 'subject': 'Mathematics', 'kind': 'Unit 7 test',
             'format': 'timed_test', 'score': 71, 'body': 'Used the extended-time accommodation for the first time.'},
            {'date': '2026-05-21', 'subject': 'Visual Arts', 'kind': 'Final exhibition',
             'format': 'project', 'score': 97, 'body': 'Sculpture and process journal both complete.'},
        ],
        'sis': [
            {'date': '2025-09-02', 'kind': 'enrollment', 'title': 'Enrolled, grade 10',
             'body': 'Continuing student. Schedule: periods 1, 3, 4, 6, 8. Section 504 flag active.'},
            {'date': '2026-02-05', 'kind': 'schedule_change', 'title': 'Schedule note',
             'body': 'Request to move the period 4 seat to the front row, approved. Movement break '
                     'pass issued for periods 1, 3 and 4.'},
        ],
        'documents': [
            {'date': '2025-09-15', 'kind': '504_plan', 'title': 'Section 504 plan',
             'body': 'Eligibility: attention deficit hyperactivity disorder, combined presentation, '
                     'documented by an outside evaluation dated 2024-05-02.\n\n'
                     'Accommodations:\n'
                     '- Extended time (1.5x) on all timed assessments.\n'
                     '- Scheduled movement breaks, one per instructional block over 25 minutes.\n'
                     '- Instructions chunked and given in writing as well as aloud.\n'
                     '- Preferential seating away from the door and window.\n'
                     '- Where the standard allows it, mastery may be demonstrated by project or '
                     'performance in place of a timed test.\n\n'
                     'Review date: 2026-02-13. All teachers of record notified.'},
            {'date': '2026-02-13', 'kind': '504_review', 'title': 'Section 504 annual review',
             'body': 'Team notes that the extended-time accommodation was used once in the first '
                     'semester. Student reports not wanting to be walked to a separate room in front '
                     'of the class. Team agrees the accommodation will be offered in advance and in '
                     'writing rather than at the desk. Project-based mastery option retained; the '
                     'gap between project and timed-test results is noted in the file without a '
                     'conclusion drawn.'},
            {'date': '2026-01-16', 'kind': 'report_card', 'title': 'Semester 1 report card',
             'body': 'Algebra II C-. World Literature C. U.S. History B. Studio Art A. Computer '
                     'Science A. Teacher comment (Okafor): "Two of these grades were earned by the '
                     'same brain."'},
        ],
        'observations': [
            {'date': '2025-10-14', 'teacher': 'boyd', 'title': 'Fourth period',
             'body': 'They are on their feet by minute twelve of any lecture. Not defiant, just gone. '
                     'When I switched to the group task they ran their table and finished first.'},
            {'date': '2026-01-13', 'teacher': 'okafor', 'title': 'Sixth period studio',
             'body': 'Forty minutes without looking up, then asked to stay through lunch to finish '
                     'the mould. I have never written them up. Mr. Boyd has written them up nine times.'},
            {'date': '2026-05-07', 'teacher': 'ramirez', 'title': 'First period',
             'body': 'On the whiteboard at the back of the room they solved the extension problem I '
                     'had not taught yet. On the test the week before they scored a 71. I do not '
                     'think the test is measuring what I want it to measure.'},
        ],
        'ai_tutor': [
            {'date': '2025-09-24', 'hour': 16, 'minute': 30,
             'body': 'can you explain this as a thing i would build instead of an equation'},
            {'date': '2025-11-05', 'hour': 20, 'minute': 15,
             'body': 'is there a video of this, the reading is four pages and i keep restarting it'},
            {'date': '2026-01-21', 'hour': 21, 'minute': 40,
             'body': 'i know all of this. how do i get it out of my head and onto paper in 45 minutes'},
            {'date': '2026-03-11', 'hour': 19, 'minute': 55,
             'body': 'give me the whole unit as one diagram, not a list'},
            {'date': '2026-04-29', 'hour': 16, 'minute': 10,
             'body': 'what would happen if i built a physical model of this instead of writing the essay'},
        ],
        'ai_tutor_fill': {
            'count': 13,
            'hour_weights': {16: 3.0, 17: 2.5, 19: 3.0, 20: 3.0, 21: 2.0},
            'bodies': [
                'break this into steps, small ones',
                'can you make this into a checklist',
                'why does this matter, i will remember it if i know why',
                'i lost the thread halfway through, start from the middle',
                'is there a hands on version of this problem',
                'give me the answer first and then the reasoning',
            ],
        },
        'parent_input': [
            {'date': '2025-12-02', 'author': 0, 'title': 'Note from home',
             'body': 'Timed tests wreck them. They knew all of that material at the kitchen table the '
                     'night before, out loud, unprompted, while building something out of cardboard.'},
            {'date': '2026-03-17', 'author': 0, 'title': 'Note from home',
             'body': 'The referrals all come from the same two class periods. I have the emails. I am '
                     'not saying anyone is wrong, I am saying it is the same two periods every time.'},
        ],
        'student_input': [
            {'date': '2025-11-11', 'title': 'What I want you to know',
             'body': 'I can do the thing. I cannot do the thing while a clock is running and forty '
                     'people are quiet.'},
            {'date': '2026-04-15', 'title': 'What I want you to know',
             'body': 'I am not trying to annoy Mr. Boyd. By minute ten my legs are going whether I '
                     'want them to or not. In studio it never happens because my hands are busy.'},
        ],
    },

    # -----------------------------------------------------------------
    # 5. Sam Nakamura — mid-year move, regression after.
    # Signals: prior-school records stop in November and a transfer lands
    # 2025-12-01; scores fall through December-February and partly
    # recover by spring; engagement records only start at the transfer and
    # are flat and low with almost no variance; observations of
    # withdrawal; a guardian note about why they moved.
    # -----------------------------------------------------------------
    {
        'key': 'sam',
        'first': 'Sam', 'last': 'Nakamura', 'pronouns': 'he/him',
        'grade': '11', 'dob': '2009-04-18', 'seed': 1005,
        'classrooms': ['lit', 'hist', 'art', 'phys', 'cs'],
        'guardians': [
            {'first': 'Yuki', 'last': 'Nakamura', 'relationship': 'mother'},
            {'first': 'Grace', 'last': 'Delaney', 'relationship': 'stepmother'},
        ],
        'engagement': {
            'base': {3: 2.2, 4: 2.1, 6: 2.3, 7: 2.4, 8: 2.2},
            'trend': 0.7, 'jitter': 0.2, 'per_week': 3,
            'start': '2025-12-01',
        },
        'absences': {
            'count': 11,
            'weights': {'month': {12: 3.0, 1: 4.0, 2: 3.0}},
            'tardies': 4,
            'tardy_weights': {'month': {12: 3.0, 1: 3.0}},
        },
        'behavior': {
            'count': 3, 'kind': 'concern', 'severity': 1,
            'period_weights': {3: 1.0, 4: 1.0, 7: 1.0},
            'weights': {'month': {12: 3.0, 1: 3.0, 2: 2.0}},
            'bodies': [
                'Did not respond when called on. No disruption. Logged so someone else sees it.',
                'Declined the group task and worked alone. Second time this month.',
                'Sat through the whole period without taking the notebook out of the bag.',
            ],
        },
        'assessments': [
            {'date': '2025-09-26', 'subject': 'Science', 'kind': 'Physics unit 1 test (Fairbrook High School)',
             'format': 'timed_test', 'score': 88,
             'body': 'Record received in the transfer file from Fairbrook High School.'},
            {'date': '2025-10-24', 'subject': 'Mathematics', 'kind': 'Precalculus unit test (Fairbrook High School)',
             'format': 'timed_test', 'score': 90,
             'body': 'Record received in the transfer file from Fairbrook High School.'},
            {'date': '2025-11-14', 'subject': 'English', 'kind': 'Literary analysis (Fairbrook High School)',
             'format': 'project', 'score': 86,
             'body': 'Record received in the transfer file from Fairbrook High School.'},
            {'date': '2025-12-12', 'subject': 'Science', 'kind': 'Physics unit 3 test',
             'format': 'timed_test', 'score': 71,
             'body': 'First assessment here. The unit assumed a lab sequence he has not done.'},
            {'date': '2026-01-23', 'subject': 'Science', 'kind': 'Physics semester exam',
             'format': 'timed_test', 'score': 64,
             'body': 'Lowest of the year. Two whole sections left blank rather than attempted.'},
            {'date': '2026-02-20', 'subject': 'English', 'kind': 'Comparative essay',
             'format': 'project', 'score': 67,
             'body': 'Submitted, thin, on time. Half the length of the November piece in his file.'},
            {'date': '2026-03-20', 'subject': 'Science', 'kind': 'Physics unit 5 test',
             'format': 'timed_test', 'score': 74, 'body': 'Attempted every section this time.'},
            {'date': '2026-04-17', 'subject': 'Computer Science', 'kind': 'Team project',
             'format': 'project', 'score': 79,
             'body': 'Worked in a pair for the first time since he arrived.'},
            {'date': '2026-05-15', 'subject': 'Science', 'kind': 'Physics final exam',
             'format': 'timed_test', 'score': 83,
             'body': 'Back within five points of where his Fairbrook record had him in the autumn.'},
        ],
        'sis': [
            {'date': '2025-09-02', 'kind': 'enrollment', 'title': 'Enrolled at Fairbrook High School, grade 11',
             'body': 'Enrolment record received later as part of the transfer file. Attendance at '
                     'Fairbrook through 2025-11-21: 1 absence. Activities: robotics team, competition '
                     'squad.'},
            {'date': '2025-11-21', 'kind': 'withdrawal', 'title': 'Withdrawn from Fairbrook High School',
             'body': 'Last day of attendance 2025-11-21. Reason recorded on the transfer form: family '
                     'relocation, out of district.'},
            {'date': '2025-12-01', 'kind': 'enrollment', 'title': f'Enrolled at {SCHOOL_NAME}, grade 11',
             'body': 'Mid-year transfer. Schedule: periods 3, 4, 6, 7, 8. Course sequence does not '
                     'align with the prior school in physics or English; no bridging plan on file.'},
        ],
        'documents': [
            {'date': '2025-12-03', 'kind': 'transfer_record', 'title': 'Transcript received from Fairbrook High School',
             'body': 'Grade 9 GPA 3.8, grade 10 GPA 3.9, grade 11 term 1 GPA 3.7. Counsellor comment '
                     'from the sending school: "Sam is a quiet, reliable student with a very close '
                     'friend group and four years on the robotics team. He will need a way in here."'},
            {'date': '2026-01-16', 'kind': 'report_card', 'title': 'Semester 1 report card',
             'body': 'Physics C-. World Literature C. U.S. History C+. Studio Art B-. Computer '
                     'Science C+. Teacher comment (Chen): "Six weeks is not enough to judge him on. '
                     'The transcript in his file and the work in my class do not look like the same '
                     'student."'},
        ],
        'observations': [
            {'date': '2025-12-09', 'teacher': 'chen', 'title': 'Seventh period, new student',
             'body': 'New in December. Sits in the back corner. He has not spoken in six class '
                     'periods, including when I put him in a lab pair. He does the work. He hands it '
                     'in. That is all I have.'},
            {'date': '2026-02-24', 'teacher': 'boyd', 'title': 'Third period',
             'body': 'Asked to work alone again. When I said the task was collaborative he said fine '
                     'and then did the whole thing himself while the others talked.'},
            {'date': '2026-04-21', 'teacher': 'chen', 'title': 'Seventh period',
             'body': 'He volunteered to demonstrate his apparatus to the class. First time. He talked '
                     'for four minutes and mentioned a competition robot he built somewhere else.'},
        ],
        'ai_tutor': [
            {'date': '2025-10-15', 'hour': 19, 'minute': 20,
             'body': 'Can you check my derivation for the momentum question? I think I dropped a sign.'},
            {'date': '2025-11-10', 'hour': 18, 'minute': 45,
             'body': 'What is a good way to explain rotational inertia to someone on my team?'},
            {'date': '2025-12-08', 'hour': 20, 'minute': 30,
             'body': 'What does this class already know that I would have missed. I started in December.'},
            {'date': '2026-01-20', 'hour': 21, 'minute': 10,
             'body': 'How far behind am I really.'},
            {'date': '2026-02-17', 'hour': 22, 'minute': 5,
             'body': 'Is it normal to be worse at something you used to be good at.'},
            {'date': '2026-04-14', 'hour': 19, 'minute': 30,
             'body': 'Can you check my derivation again, I want to be sure before I show it in class.'},
            {'date': '2026-05-12', 'hour': 18, 'minute': 50,
             'body': 'Does this school have a robotics team, and if not how would someone start one.'},
        ],
        'ai_tutor_fill': {
            'count': 9,
            'hour_weights': {18: 3.0, 19: 3.0, 20: 2.0, 21: 1.5},
            'weights': {'month': {9: 3.0, 10: 3.0, 11: 3.0, 12: 0.2, 1: 0.2, 2: 0.3,
                                  3: 1.0, 4: 2.0, 5: 2.5}},
            'bodies': [
                'Check my working on this problem please.',
                'What is the standard way to set this up.',
                'Which unit does this topic normally come from.',
                'Can you give me the prerequisites for this chapter.',
                'Is there a summary of what a class would cover before this.',
            ],
        },
        'parent_input': [
            {'date': '2025-12-05', 'author': 0, 'title': 'Note from home',
             'body': 'We moved in November for my mother\'s care. It was not planned and it was fast. '
                     'Sam left a robotics team and a best friend he has had since he was seven. He '
                     'tells me school is fine every day in exactly the same words.'},
            {'date': '2026-04-28', 'author': 1, 'title': 'Note from home',
             'body': 'He asked whether he could invite someone over. That has not happened since '
                     'November.'},
        ],
        'student_input': [
            {'date': '2026-01-15', 'title': 'What I want you to know',
             'body': 'At Fairbrook we did this unit in September. Here it was in October and I was '
                     'not here for it. Nobody asked me what I had already done.'},
            {'date': '2026-05-11', 'title': 'What I want you to know',
             'body': 'It is getting better. Physics makes sense again. I still do not really know '
                     'anyone outside of seventh period.'},
        ],
    },

    # -----------------------------------------------------------------
    # 6. Priya Raghunathan — gifted and disengaged.
    # Signals: near-perfect tests sitting next to a homework completion
    # rate in the thirties; behaviour notes that are all boredom and no
    # conflict; tutor questions miles outside the syllabus; engagement in
    # the floor everywhere except the period 8 elective.
    # -----------------------------------------------------------------
    {
        'key': 'priya',
        'first': 'Priya', 'last': 'Raghunathan', 'pronouns': 'she/her',
        'grade': '11', 'dob': '2009-11-05', 'seed': 1006,
        'classrooms': ['alg2', 'lit', 'hist', 'phys', 'cs'],
        'guardians': [
            {'first': 'Anjali', 'last': 'Raghunathan', 'relationship': 'mother'},
            {'first': 'Vikram', 'last': 'Raghunathan', 'relationship': 'father'},
        ],
        'engagement': {
            'base': {1: 2.0, 3: 1.8, 4: 1.7, 7: 2.3, 8: 4.8},
            'trend': -0.2, 'jitter': 0.35, 'per_week': 3,
        },
        'absences': {'count': 4, 'tardies': 11,
                     'tardy_weights': {'weekday': {0: 1.5}}},
        'behavior': {
            'count': 15, 'kind': 'off_task', 'severity': 1,
            'period_weights': {3: 4.0, 4: 4.0, 1: 3.0, 7: 2.0, 8: 0.05},
            'bodies': [
                'Reading a book about game theory under the desk during the review session.',
                'Finished the packet in nine minutes and then talked for the remaining thirty.',
                'Asked whether the assignment was optional. Not rudely. She genuinely wanted to know.',
                'Doing physics problems during the history reading.',
                'Head on the desk during the re-teach. Answered the check question correctly from that position.',
                'Drew a proof on the desk in pencil during the lecture.',
                'Asked if she could skip to the end of the unit. Asked again the next day.',
                'Left the room at the bell without the homework sheet. Told me she did not need it.',
            ],
        },
        'assessments': [
            {'date': '2025-09-19', 'subject': 'Mathematics', 'kind': 'Unit 1 test',
             'format': 'timed_test', 'score': 100, 'body': 'Perfect, in twenty-two minutes of a fifty-minute period.'},
            {'date': '2025-09-30', 'subject': 'Mathematics', 'kind': 'Homework completion, September',
             'format': 'homework', 'score': 40,
             'body': 'Eight of twenty assignments submitted.',
             'data': {'assigned': 20, 'submitted': 8}},
            {'date': '2025-10-24', 'subject': 'Science', 'kind': 'Physics unit 2 test',
             'format': 'timed_test', 'score': 98, 'body': 'One arithmetic slip, method flawless.'},
            {'date': '2025-10-31', 'subject': 'Mathematics', 'kind': 'Homework completion, October',
             'format': 'homework', 'score': 32,
             'body': 'Seven of twenty-two assignments submitted.',
             'data': {'assigned': 22, 'submitted': 7}},
            {'date': '2025-12-12', 'subject': 'Mathematics', 'kind': 'Semester exam',
             'format': 'timed_test', 'score': 99, 'body': 'Highest in the grade.'},
            {'date': '2025-12-19', 'subject': 'English', 'kind': 'Homework completion, semester 1',
             'format': 'homework', 'score': 29,
             'body': 'Eleven of thirty-eight assignments submitted across the semester.',
             'data': {'assigned': 38, 'submitted': 11}},
            {'date': '2026-01-23', 'subject': 'Science', 'kind': 'Physics semester exam',
             'format': 'timed_test', 'score': 97, 'body': 'Second highest in the grade.'},
            {'date': '2026-02-13', 'subject': 'Computer Science', 'kind': 'Capstone milestone',
             'format': 'project', 'score': 99,
             'body': 'Wrote a compiler for a toy language. The brief asked for a calculator.'},
            {'date': '2026-03-27', 'subject': 'Mathematics', 'kind': 'Unit 6 test',
             'format': 'timed_test', 'score': 100, 'body': 'Perfect again.'},
            {'date': '2026-04-30', 'subject': 'Mathematics', 'kind': 'Homework completion, spring term',
             'format': 'homework', 'score': 35,
             'body': 'Fourteen of forty assignments submitted.',
             'data': {'assigned': 40, 'submitted': 14}},
            {'date': '2026-05-22', 'subject': 'Science', 'kind': 'Physics final exam',
             'format': 'timed_test', 'score': 98, 'body': 'No change all year.'},
            {'date': '2026-05-29', 'subject': 'Computer Science', 'kind': 'Final project',
             'format': 'project', 'score': 100,
             'body': 'Only assignment she has ever submitted early. Twice the required scope.'},
        ],
        'sis': [
            {'date': '2025-09-02', 'kind': 'enrollment', 'title': 'Enrolled, grade 11',
             'body': 'Continuing student. Schedule: periods 1, 3, 4, 7, 8. Advanced learner '
                     'identification on file since grade 4.'},
            {'date': '2026-02-05', 'kind': 'program_flag', 'title': 'Course placement note',
             'body': 'Request submitted to test out of the grade 11 mathematics sequence. Returned: '
                     'no dual-enrolment seat available this term. Counsellor note: "Please revisit in '
                     'the autumn."'},
        ],
        'documents': [
            {'date': '2025-09-25', 'kind': 'advanced_learner_plan', 'title': 'Advanced learner plan',
             'body': 'Identification: grade 4, verbal and quantitative reasoning both above the 99th '
                     'percentile. Plan: acceleration where scheduling allows; independent study '
                     'option in mathematics and computer science; enrichment in place of repeated '
                     'practice where mastery is already demonstrated. Note: the independent study '
                     'option was not scheduled this year, no seat.'},
            {'date': '2026-01-16', 'kind': 'report_card', 'title': 'Semester 1 report card',
             'body': 'Algebra II B (test average 99, homework average 36). World Literature C+. '
                     'U.S. History C. Physics B+. Computer Science A. Teacher comment (Okafor): '
                     '"In period 8 she is the most alive student in the building. I have read what '
                     'her other teachers wrote and I do not recognise the student they describe."'},
        ],
        'observations': [
            {'date': '2025-11-06', 'teacher': 'ramirez', 'title': 'First period',
             'body': 'She has a 99 test average and a 36 per cent homework completion rate. I asked '
                     'her about it. She said the homework was already answered by the test.'},
            {'date': '2026-02-11', 'teacher': 'boyd', 'title': 'Third period',
             'body': 'She has never once been rude and I have written her up four times. It is always '
                     'the same thing: she is done, and there are thirty minutes left, and there is '
                     'nothing in this room for her to do.'},
            {'date': '2026-03-18', 'teacher': 'okafor', 'title': 'Eighth period',
             'body': 'She stayed ninety minutes after the bell to argue about type systems. She has '
                     'not handed in a single worksheet all year and she has shipped four things '
                     'nobody assigned.'},
        ],
        'ai_tutor': [
            {'date': '2025-09-17', 'hour': 22, 'minute': 15,
             'body': 'Can you explain Gödel\'s first incompleteness theorem to someone who has done calculus?'},
            {'date': '2025-10-21', 'hour': 21, 'minute': 40,
             'body': 'Why does the Riemann rearrangement theorem not break physics.'},
            {'date': '2025-12-03', 'hour': 23, 'minute': 5,
             'body': 'What is the actual state of the P versus NP question, not the popular version.'},
            {'date': '2026-01-14', 'hour': 22, 'minute': 50,
             'body': 'My uncle sent me a problem set on measure theory. Can you check problem 3.'},
            {'date': '2026-02-25', 'hour': 21, 'minute': 30,
             'body': 'Is there a reason type inference is undecidable in some systems and not others.'},
            {'date': '2026-04-08', 'hour': 23, 'minute': 20,
             'body': 'How would I write a garbage collector. Assume I have already written a parser.'},
            {'date': '2026-05-13', 'hour': 22, 'minute': 35,
             'body': 'What would I have to learn, in order, to read a paper on homotopy type theory.'},
        ],
        'ai_tutor_fill': {
            'count': 12,
            'hour_weights': {20: 2.0, 21: 3.5, 22: 3.5, 23: 2.5},
            'bodies': [
                'Give me the hardest version of this problem you have.',
                'What comes after this topic, two courses later.',
                'Is there a shorter proof of this.',
                'Explain the general case, not the example.',
                'What is the open problem in this area.',
                'Skip the intuition, give me the formal statement.',
            ],
        },
        'parent_input': [
            {'date': '2025-10-28', 'author': 0, 'title': 'Note from home',
             'body': 'She reads three books a week and will not do twenty minutes of worksheets. Her '
                     'uncle sends her problem sets from his university course and she does those at '
                     'midnight, for nothing, for no grade.'},
            {'date': '2026-03-10', 'author': 1, 'title': 'Note from home',
             'body': 'We are not asking anyone to give her an A. We are asking whether there is '
                     'anything in the timetable that she has not already finished.'},
        ],
        'student_input': [
            {'date': '2026-02-04', 'title': 'What I want you to know',
             'body': 'The computer science elective is the only place in the building where I do not '
                     'already know how it ends.'},
            {'date': '2026-05-06', 'title': 'What I want you to know',
             'body': 'I am not bored of learning. I am bored of proving to five different adults that '
                     'I already learned it.'},
        ],
    },
]


# ---------------------------------------------------------------------------
# Filler students — light records, present so rosters look like real rosters.
# ---------------------------------------------------------------------------

FILLERS = [
    {'key': 'nia_carter', 'first': 'Nia', 'last': 'Carter', 'grade': '11',
     'guardian': None},  # shares Deshawn's guardian, wired by 'also_guardian_of'
    {'key': 'f02', 'first': 'Oliver', 'last': 'Brennan', 'grade': '9'},
    {'key': 'f03', 'first': 'Amara', 'last': 'Diallo', 'grade': '9'},
    {'key': 'f04', 'first': 'Tobias', 'last': 'Lindqvist', 'grade': '9'},
    {'key': 'f05', 'first': 'Rosa', 'last': 'Villanueva', 'grade': '9'},
    {'key': 'f06', 'first': 'Kenji', 'last': 'Watanabe', 'grade': '9'},
    {'key': 'f07', 'first': 'Harper', 'last': 'Ellsworth', 'grade': '9'},
    {'key': 'f08', 'first': 'Malik', 'last': 'Osei', 'grade': '9'},
    {'key': 'f09', 'first': 'Fatima', 'last': 'Haddad', 'grade': '10'},
    {'key': 'f10', 'first': 'Cormac', 'last': 'Byrne', 'grade': '10'},
    {'key': 'f11', 'first': 'Svetlana', 'last': 'Petrov', 'grade': '10'},
    {'key': 'f12', 'first': 'Andre', 'last': 'Beaumont', 'grade': '10'},
    {'key': 'f13', 'first': 'Leilani', 'last': 'Kahale', 'grade': '10'},
    {'key': 'f14', 'first': 'Ezra', 'last': 'Feldman', 'grade': '10'},
    {'key': 'f15', 'first': 'Nadia', 'last': 'Rahimi', 'grade': '10'},
    {'key': 'f16', 'first': 'Beatriz', 'last': 'Fonseca', 'grade': '10'},
    {'key': 'f17', 'first': 'Declan', 'last': 'Moriarty', 'grade': '11'},
    {'key': 'f18', 'first': 'Yasmin', 'last': 'Chaudhry', 'grade': '11'},
    {'key': 'f19', 'first': 'Theo', 'last': 'Anagnos', 'grade': '11'},
    {'key': 'f20', 'first': 'Camille', 'last': 'Dubois', 'grade': '11'},
    {'key': 'f21', 'first': 'Rashid', 'last': 'Al-Amin', 'grade': '11'},
    {'key': 'f22', 'first': 'Ingrid', 'last': 'Halvorsen', 'grade': '11'},
    {'key': 'f23', 'first': 'Junho', 'last': 'Park', 'grade': '11'},
    {'key': 'f24', 'first': 'Talia', 'last': 'Mensah', 'grade': '10'},
]

# Guardians shared by two filler students, so the guardian view has something
# to switch between.
FILLER_GUARDIANS = [
    {'first': 'Siobhan', 'last': 'Byrne', 'relationship': 'mother',
     'students': ['f10', 'f17']},
    {'first': 'Nadeem', 'last': 'Chaudhry', 'relationship': 'father',
     'students': ['f18', 'f15']},
    {'first': 'Anneke', 'last': 'Halvorsen', 'relationship': 'mother',
     'students': ['f22', 'f11']},
]

FILLER_ASSESSMENT_KINDS = [
    ('Mathematics', 'Unit test', 'timed_test'),
    ('Science', 'Lab practical', 'project'),
    ('English', 'Writing task', 'project'),
    ('Social Studies', 'Unit exam', 'timed_test'),
    ('Mathematics', 'Semester exam', 'timed_test'),
    ('Science', 'Unit quiz', 'timed_test'),
]

FILLER_BEHAVIOR_BODIES = [
    'Talking during independent work. Redirected once.',
    'Phone out during the lesson. Handed it over without argument.',
    'Late to class with no pass.',
    'Off task for the first ten minutes, fine after a reminder.',
]

FILLER_OBSERVATION_BODIES = [
    'Steady all term. Asks for help when stuck, which not everyone does.',
    'Quiet in whole-class discussion and much more forthcoming in a group of four.',
    'Has got noticeably faster at the warm-up problems since the autumn.',
    'Works well with anyone I seat them next to.',
    'Would rather present than write. Presented well.',
]

FILLER_TUTOR_BODIES = [
    'Can you explain this one more time?',
    'What is the formula for this again?',
    'Is my answer to question 4 right?',
    'Help me plan this essay.',
    'What does this word mean in the reading?',
]
