/**
 * Synthetic fixture data for the Student Passport demo.
 *
 * Every student, record and narrative in this file is invented. No real
 * student is described here and none of this data came from a real system.
 *
 * Only `client.ts` may import this module. Components read data through the
 * client so the fixtures can be replaced with HTTP calls in one place.
 *
 * The six hero students follow authored story arcs. Their records are
 * correlated on purpose: the cause behind each arc is meant to be inferable
 * from the pattern across sources, and is never stated in any single record.
 */

import type {
  Answer,
  Classroom,
  Guardian,
  Me,
  Passport,
  PassportSections,
  Role,
  Student,
  StudentRecord,
} from './types';
import {
  MONTH_LABELS,
  PERIODS,
  YEAR_END_MS,
  YEAR_START_MS,
  monthOf,
  weekdayOf,
} from '../lib/school';

// ---------------------------------------------------------------------------
// School calendar
// ---------------------------------------------------------------------------

/** School weekdays bucketed by month index, 0 = September. */
const daysByMonth: string[][] = MONTH_LABELS.map(() => []);
for (let t = YEAR_START_MS; t <= YEAR_END_MS; t += 86_400_000) {
  const d = new Date(t);
  const weekday = d.getUTCDay();
  if (weekday === 0 || weekday === 6) continue;
  const iso = d.toISOString().slice(0, 10);
  daysByMonth[monthOf(iso)].push(iso);
}

/** Deterministic PRNG (mulberry32) so the demo looks the same every reload. */
function makeRng(seed: number): () => number {
  let a = seed;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function pick<T>(items: T[], r: () => number): T {
  return items[Math.floor(r() * items.length)];
}

function clamp(n: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, n));
}

// ---------------------------------------------------------------------------
// Arc definitions
// ---------------------------------------------------------------------------

interface SubjectArc {
  /** Series name on the performance chart. */
  name: string;
  /** Assessment kind, e.g. "unit test". Rotates when omitted. */
  kind?: string;
  /** Score for month index 0 (September) through 9 (June). */
  score: (month: number) => number;
}

interface Extra {
  source: StudentRecord['source'];
  kind: string;
  date: string;
  title: string;
  body: string;
  data?: Record<string, unknown>;
  author?: string;
}

interface ArcSpec {
  id: number;
  first_name: string;
  last_name: string;
  grade: string;
  pronouns: string;
  date_of_birth: string;
  guardians: Guardian[];
  subjects: SubjectArc[];
  /** Points added for a project and taken off a timed test. */
  format_swing?: number;
  absences_per_month: number;
  /** Share of absences forced onto a Monday, 0 to 1. */
  monday_bias?: number;
  /** Chance of a nurse visit on the school day before an assessment. */
  nurse_before_assessment?: number;
  behavior_per_month: number;
  /** Periods incidents cluster in. */
  behavior_periods: number[];
  behavior_kinds: string[];
  /** Mean engagement rating by period; index 0 is period 1. */
  engagement_by_period: number[];
  /** Change in mean engagement per month. */
  engagement_trend?: number;
  /** A one-off change in engagement from a given month onward. */
  engagement_step?: { month: number; delta: number };
  sections: PassportSections;
  extras: Extra[];
}

const ROTATING_KINDS = ['quiz', 'unit test', 'project', 'timed test'];

const HERO_ARCS: ArcSpec[] = [
  {
    id: 1,
    first_name: 'Maya',
    last_name: 'Okonkwo',
    grade: '10',
    pronouns: 'she/her',
    date_of_birth: '2010-03-14',
    guardians: [{ id: 301, name: 'Ngozi Okonkwo', relationship: 'mother' }],
    subjects: [
      { name: 'AP Biology', score: (m) => 93 + Math.min(m, 4) * 0.5 },
      { name: 'English 10', score: (m) => 91 + (m % 3) },
      { name: 'Geometry', score: (m) => 96 - (m % 2) },
    ],
    absences_per_month: 0.6,
    nurse_before_assessment: 0.55,
    behavior_per_month: 0.1,
    behavior_periods: [3],
    behavior_kinds: ['off task'],
    engagement_by_period: [3.9, 3.8, 3.7, 3.6, 3.7, 3.5, 3.4],
    engagement_trend: -0.16,
    sections: {
      overview: {
        teacher_voice:
          'Maya turns in polished work ahead of every deadline and her scores have not moved off the top of the range all year. What has changed is everything around the work: she asks fewer questions in class than she did in September, checks answers with me twice before submitting, and has started apologising for work that needs no apology.',
        guardian_voice:
          'Her mother reports that Maya is up well past midnight most school nights and will not go to bed until an assignment "feels finished". She describes her as hard on herself and says the household treats a B as a non-event, though Maya does not.',
        student_voice:
          'Maya describes herself as behind even in classes she leads. In her own words she is "fine, just tired", and she says she prefers to sort problems out on her own before asking anyone.',
      },
      how_they_learn:
        'Maya works best from written material she can re-read, and she prepares far more than a task requires. She is most engaged early in the day and her attention falls off through the afternoon, a slope that has steepened month by month. She rarely asks for help in front of peers but uses the AI tutor heavily in private, mostly late at night.',
      performance:
        'Scores are high and stable across all three subjects, with no month below 90. Achievement is not the signal to watch here — the surrounding records move while the scores do not.',
      behavior:
        'No referrals and no conflict on record. The only behaviour-adjacent entries are health-office visits, which fall almost entirely on the school day before a scheduled assessment.',
    },
    extras: [
      {
        source: 'sis',
        kind: 'enrollment',
        date: '2025-09-02',
        title: 'Enrolled, grade 10',
        body: 'Continuing student. Course load: AP Biology, English 10, Geometry, Spanish 2, Concert Band.',
      },
      {
        source: 'document',
        kind: 'report card',
        date: '2026-01-23',
        title: 'Semester 1 report card',
        body: 'AP Biology A, English 10 A, Geometry A. Teacher comment: "A pleasure to teach. Consistently exceeds the standard."',
      },
      {
        source: 'observation',
        kind: 'teacher observation',
        date: '2025-11-18',
        title: 'Before the unit test',
        body: 'Found Maya in the hallway before third period, crying, saying she had not studied enough. She sat the test twenty minutes later and scored 96, the highest in the section. When I passed it back she asked what she had lost the points on.',
        author: 'Ms. Rivera',
      },
      {
        source: 'observation',
        kind: 'teacher observation',
        date: '2026-03-05',
        title: 'Group work',
        body: 'Maya took the whole write-up for her lab group rather than split it. She told her partners it was "faster this way". The work was excellent and she looked exhausted doing it.',
        author: 'Ms. Rivera',
      },
      {
        source: 'ai_tutor',
        kind: 'tutor session',
        date: '2025-10-14',
        title: 'Cell respiration, 11:42pm',
        body: 'Asked the tutor to check a completed answer four times, each time rewording the same question. Final message: "is this good enough to hand in".',
        data: { hour: 23, minute: 42, turns: 14 },
      },
      {
        source: 'ai_tutor',
        kind: 'tutor session',
        date: '2025-12-09',
        title: 'Essay thesis, 1:05am',
        body: 'Asked whether a thesis was "actually original or just obvious". Rewrote it six times in one session.',
        data: { hour: 1, minute: 5, turns: 22 },
      },
      {
        source: 'ai_tutor',
        kind: 'tutor session',
        date: '2026-02-11',
        title: 'Geometry proof, 12:20am',
        body: 'Proof was correct on the first attempt. Spent the remaining session asking whether a different method would have been "the one the teacher wanted".',
        data: { hour: 0, minute: 20, turns: 18 },
      },
      {
        source: 'ai_tutor',
        kind: 'tutor session',
        date: '2026-04-22',
        title: 'AP review, 11:58pm',
        body: 'Asked for a practice set "harder than the real exam". Worked through it, then asked what score would be "safe".',
        data: { hour: 23, minute: 58, turns: 31 },
      },
      {
        source: 'parent_input',
        kind: 'guardian note',
        date: '2026-01-12',
        title: 'From home',
        body: 'She is doing well on paper so I feel silly writing this. She is not sleeping. Her light is on at 1am and she is up again at 6. I have told her a B would be fine and she says she knows. Nothing I say seems to land.',
        author: 'Ngozi Okonkwo',
      },
      {
        source: 'student_input',
        kind: 'student note',
        date: '2026-02-02',
        title: 'What I want you to know',
        body: 'I would rather have the reading list early than get extra time later. I do not like being called on when I have not checked my answer first.',
        author: 'Maya Okonkwo',
      },
    ],
  },
  {
    id: 2,
    first_name: 'Deshawn',
    last_name: 'Carter',
    grade: '9',
    pronouns: 'he/him',
    date_of_birth: '2011-07-22',
    guardians: [{ id: 302, name: 'Renata Carter', relationship: 'mother' }],
    subjects: [
      { name: 'Algebra I', score: (m) => 82 + m * 0.7 },
      { name: 'English 9', score: (m) => 79 + m * 0.5 },
    ],
    absences_per_month: 2.4,
    monday_bias: 0.72,
    behavior_per_month: 2.1,
    behavior_periods: [4],
    behavior_kinds: ['off task', 'head down', 'short with a peer', 'left class'],
    engagement_by_period: [2.9, 2.8, 2.6, 2.2, 4.3, 4.5, 4.4],
    sections: {
      overview: {
        teacher_voice:
          'Deshawn does strong work on the days he is in the room. The difficulty is not ability and it is not attitude — it is that his week starts badly and his mornings are harder than his afternoons. By fifth period he is one of the most willing contributors in the class.',
        guardian_voice:
          'His mother changed to a night shift in November and writes that mornings at home are now handled by Deshawn himself. She asks that he not be penalised for lateness on Mondays and mentions that the weekend is "the long stretch".',
        student_voice:
          'Deshawn says school is "alright, after lunch". He says he does not like being asked what is wrong in front of people and would rather be given the work and left to it.',
      },
      how_they_learn:
        'Deshawn learns quickly from worked examples and holds on to what he has understood. His engagement pattern is unusually sharp: low through the morning, with a marked and sustained rise from fifth period onward. Work set in the afternoon comes back done; work set in the morning often does not.',
      performance:
        'Scores climb steadily in both subjects across the year, from the low 80s to the high 80s in Algebra. Performance tracks attendance rather than difficulty — the material is not the obstacle.',
      behavior:
        'Incidents are frequent but narrow. Almost every flag falls in fourth period, and the record after lunch is close to clean. None of the entries describe conflict; most describe withdrawal or irritability.',
    },
    extras: [
      {
        source: 'sis',
        kind: 'enrollment',
        date: '2025-09-02',
        title: 'Enrolled, grade 9',
        body: 'First year at this school. Course load: Algebra I, English 9, Physical Science, World History, PE.',
      },
      {
        source: 'parent_input',
        kind: 'guardian note',
        date: '2025-11-10',
        title: 'Change at home',
        body: 'I moved onto nights at the warehouse from the first of the month, so I am not home for the mornings any more. Deshawn gets himself out. Mondays are the hard one after the weekend. Please tell me directly if he is falling behind, I will sort it.',
        author: 'Renata Carter',
      },
      {
        source: 'observation',
        kind: 'teacher observation',
        date: '2025-10-06',
        title: 'Fourth period',
        body: 'Head on the desk for most of the period, not disruptive, would not start the task. Same student was leading his table group two periods later.',
        author: 'Mr. Halloran',
      },
      {
        source: 'observation',
        kind: 'teacher observation',
        date: '2026-02-23',
        title: 'Sixth period',
        body: 'Deshawn re-explained the whole factoring method to two classmates, unprompted, and got it right. Asked if he could take the practice set home.',
        author: 'Ms. Rivera',
      },
      {
        source: 'ai_tutor',
        kind: 'tutor session',
        date: '2026-01-15',
        title: 'Factoring practice, 4:10pm',
        body: 'Worked through eleven problems without hints. Asked at the end whether he could get "more of these ones".',
        data: { hour: 16, minute: 10, turns: 24 },
      },
      {
        source: 'ai_tutor',
        kind: 'tutor session',
        date: '2026-03-18',
        title: 'Essay structure, 3:50pm',
        body: 'Asked how to plan a five-paragraph essay "so I can finish it in one go tonight".',
        data: { hour: 15, minute: 50, turns: 9 },
      },
      {
        source: 'student_input',
        kind: 'student note',
        date: '2026-03-02',
        title: 'What I want you to know',
        body: 'If I miss a Monday just give me the sheet, I can catch up. I do not need to be asked about it in front of everyone.',
        author: 'Deshawn Carter',
      },
      {
        source: 'document',
        kind: 'report card',
        date: '2026-01-23',
        title: 'Semester 1 report card',
        body: 'Algebra I B, English 9 B-. Attendance flagged: 14 absences, 9 of them Mondays. Teacher comment: "Capable of much more with consistent attendance."',
      },
    ],
  },
  {
    id: 3,
    first_name: 'Alina',
    last_name: 'Restrepo',
    grade: '9',
    pronouns: 'she/her',
    date_of_birth: '2011-01-30',
    guardians: [{ id: 303, name: 'Marisol Restrepo', relationship: 'mother' }],
    subjects: [
      { name: 'Reading', score: (m) => 51 + m * 3.4 },
      { name: 'Math 9', score: (m) => 90 + m * 0.6 },
    ],
    absences_per_month: 0.5,
    behavior_per_month: 0.15,
    behavior_periods: [3],
    behavior_kinds: ['off task'],
    engagement_by_period: [2.9, 4.5, 3.0, 3.1, 2.8, 4.6, 3.2],
    engagement_trend: 0.06,
    sections: {
      overview: {
        teacher_voice:
          'Alina arrived in September with almost no classroom English and has closed a large part of the reading gap in a single year. Her mathematics was strong from the first week — the language, not the content, was the barrier. She works hardest when she has someone to work with.',
        guardian_voice:
          'Her mother writes that Alina reads to her younger brother in English every evening to practise, and asks that the school send letters home in Spanish where possible.',
        student_voice:
          'Alina says maths is "the same in every language". She has asked to be seated with a partner rather than alone, and says she does not mind being wrong out loud in a small group.',
      },
      how_they_learn:
        'Alina learns fastest in pairs and small groups, and in lab periods where the task is physical before it is verbal. Her engagement is highest in second-period lab and sixth-period group work, and noticeably lower in lecture blocks. She uses the AI tutor bilingually, switching to Spanish when she wants a concept explained rather than a task checked.',
      performance:
        'Reading has climbed steeply and consistently, from the low 50s in September to the low 80s by June — the steepest sustained gain in her year group. Mathematics has been in the 90s throughout and is not a concern.',
      behavior:
        'Nothing on record beyond a single off-task note. She has twice been observed translating for a classmate without being asked.',
    },
    extras: [
      {
        source: 'sis',
        kind: 'enrollment',
        date: '2025-09-02',
        title: 'Enrolled, grade 9 — newcomer',
        body: 'New to the district. Home language Spanish. English learner services, 2 periods weekly.',
      },
      {
        source: 'document',
        kind: 'language plan',
        date: '2025-09-15',
        title: 'English learner support plan',
        body: 'Level 2 (emerging). Supports: extended time on written assessments, bilingual glossary permitted, seating with a partner. Reviewed each semester.',
      },
      {
        source: 'observation',
        kind: 'teacher observation',
        date: '2026-01-20',
        title: 'Second period lab',
        body: 'Alina finished the calculation early and then translated the whole procedure for a classmate who had not started. Nobody asked her to. Both of them finished.',
        author: 'Ms. Rivera',
      },
      {
        source: 'observation',
        kind: 'teacher observation',
        date: '2026-04-14',
        title: 'Reading conference',
        body: 'Read a page aloud that would have stopped her in October. She noticed that herself and grinned about it.',
        author: 'Mr. Halloran',
      },
      {
        source: 'ai_tutor',
        kind: 'tutor session',
        date: '2025-10-21',
        title: 'Ecuaciones lineales, 6:30pm',
        body: 'Asked in Spanish for an explanation of slope, then asked for the same explanation in English "para la clase". Worked the problems in English.',
        data: { hour: 18, minute: 30, turns: 16, language: 'es' },
      },
      {
        source: 'ai_tutor',
        kind: 'tutor session',
        date: '2026-02-17',
        title: 'Vocabulary, 7:15pm',
        body: 'Asked for the difference between "although" and "however" with examples. Used both correctly in an essay the following week.',
        data: { hour: 19, minute: 15, turns: 11, language: 'en' },
      },
      {
        source: 'parent_input',
        kind: 'guardian note',
        date: '2026-02-09',
        title: 'From home',
        body: 'Alina reads to her brother every night in English. She is proud of the reading score going up. Please send the letters in Spanish if you can, I do not want to miss anything.',
        author: 'Marisol Restrepo',
      },
      {
        source: 'student_input',
        kind: 'student note',
        date: '2026-03-10',
        title: 'What I want you to know',
        body: 'I understand more than I can say fast. Give me a second before you move on. I like working with a partner.',
        author: 'Alina Restrepo',
      },
    ],
  },
  {
    id: 4,
    first_name: 'Jordan',
    last_name: 'Whitaker',
    grade: '10',
    pronouns: 'they/them',
    date_of_birth: '2010-11-05',
    guardians: [
      { id: 304, name: 'Erin Whitaker', relationship: 'mother' },
      { id: 305, name: 'Paul Whitaker', relationship: 'father' },
    ],
    subjects: [
      { name: 'Environmental Science', score: (m) => 80 + (m % 3) },
      { name: 'World History', score: (m) => 77 + (m % 4) },
    ],
    format_swing: 17,
    absences_per_month: 0.8,
    behavior_per_month: 1.9,
    behavior_periods: [1, 3],
    behavior_kinds: [
      'out of seat',
      'calling out',
      'off task',
      'left class without permission',
    ],
    engagement_by_period: [2.3, 2.5, 2.4, 4.6, 4.7, 2.6, 4.5],
    sections: {
      overview: {
        teacher_voice:
          'Jordan is one of the sharpest students in the room when there is something in their hands. In a fifty-minute lecture block they are out of their seat within twenty minutes; in the lab next door they run the bench and other students go to them for help. The same student, the same day.',
        guardian_voice:
          'Their parents describe the 504 plan as "the thing that finally worked" and ask that movement breaks be treated as part of the plan rather than a concession. They note Jordan builds furniture at home for hours without a break.',
        student_voice:
          'Jordan says they know the material and lose it in the writing-it-down part. They have asked to show what they know by building or presenting rather than by timed test.',
      },
      how_they_learn:
        'Jordan learns by doing and holds attention indefinitely when the task is physical. Engagement is high in the lab, studio and workshop periods and low in every extended lecture block, with no month-to-month drift — it is the format, not the term. Their 504 plan allows movement breaks and extended time.',
      performance:
        'Assessment scores swing by roughly thirty points depending on format. Projects and practicals land in the mid 90s; timed written tests on the same content land in the low 60s. Reading the average alone would badly misdescribe what Jordan knows.',
      behavior:
        'Referrals cluster almost entirely in first and third period, the two long lecture blocks. Lab and studio periods are close to incident-free across the whole year.',
    },
    extras: [
      {
        source: 'sis',
        kind: 'enrollment',
        date: '2025-09-02',
        title: 'Enrolled, grade 10',
        body: 'Continuing student. Course load: Environmental Science, World History, Geometry, Studio Art, Woodshop.',
      },
      {
        source: 'document',
        kind: '504 plan',
        date: '2025-09-19',
        title: '504 plan — ADHD',
        body: 'Accommodations: extended time (1.5x) on written assessments, permitted movement breaks each period, seating near the door, assignment instructions given in writing as well as aloud, option to demonstrate mastery by project where the standard allows. Review annually.',
      },
      {
        source: 'observation',
        kind: 'teacher observation',
        date: '2025-10-28',
        title: 'Third period',
        body: 'Third time out of the seat before the halfway point of the lecture. Not disruptive to others, visibly uncomfortable. Took a movement break and came back able to work.',
        author: 'Mr. Halloran',
      },
      {
        source: 'observation',
        kind: 'teacher observation',
        date: '2026-03-11',
        title: 'Fifth period lab',
        body: 'Jordan ran the water-quality bench for the whole period, kept their own notes, and troubleshot two other groups’ equipment. Fifty minutes, no prompting, no break needed.',
        author: 'Ms. Rivera',
      },
      {
        source: 'ai_tutor',
        kind: 'tutor session',
        date: '2026-01-27',
        title: 'Nitrogen cycle, 5:05pm',
        body: 'Asked the tutor to turn the chapter into a build plan for a model. Then asked the questions back to check the model was right.',
        data: { hour: 17, minute: 5, turns: 20 },
      },
      {
        source: 'parent_input',
        kind: 'guardian note',
        date: '2025-12-03',
        title: 'From home',
        body: 'Jordan built a bookcase over the weekend, start to finish, no reminders. The plan says movement breaks so please let them take one before it becomes a referral. They know when they need it.',
        author: 'Erin Whitaker',
      },
      {
        source: 'student_input',
        kind: 'student note',
        date: '2026-02-19',
        title: 'What I want you to know',
        body: 'I am not bored, I am stuck sitting. If I can build it or say it out loud I will get full marks. Timed tests are the worst way to ask me what I know.',
        author: 'Jordan Whitaker',
      },
    ],
  },
  {
    id: 5,
    first_name: 'Sam',
    last_name: 'Nakamura',
    grade: '11',
    pronouns: 'he/him',
    date_of_birth: '2009-05-18',
    guardians: [{ id: 306, name: 'Kenji Nakamura', relationship: 'father' }],
    subjects: [
      {
        name: 'Chemistry',
        score: (m) => (m <= 2 ? 86 - m : m <= 5 ? 72 - (m - 3) * 2 : 70 + (m - 5) * 3),
      },
      {
        name: 'US History',
        score: (m) => (m <= 2 ? 84 - m : m <= 5 ? 70 - (m - 3) * 2 : 68 + (m - 5) * 3),
      },
    ],
    absences_per_month: 1.1,
    behavior_per_month: 0.4,
    behavior_periods: [2, 6],
    behavior_kinds: ['did not participate', 'off task'],
    engagement_by_period: [3.9, 4.0, 3.8, 3.9, 4.1, 3.8, 3.9],
    engagement_step: { month: 3, delta: -1.6 },
    sections: {
      overview: {
        teacher_voice:
          'Sam transferred in at the end of November and the drop is visible in every source at once. He was a B-plus student at his previous school, fell to the high 60s over his first term here, and has climbed back into the high 70s since March. He is quiet in a way that reads as careful rather than disengaged.',
        guardian_voice:
          'His father writes that the move was for work, mid-year, and that Sam left a school he had been at since kindergarten. He says Sam has not complained once, which worries him more than complaining would.',
        student_voice:
          'Sam says the content is not the problem, the sequencing is — his previous school covered stoichiometry a term later. He says he "does not really know anyone in fourth period yet".',
      },
      how_they_learn:
        'Sam is an independent worker who reads ahead when he knows what is coming. His engagement was even and high across all periods before the move and dropped by roughly a point and a half across the board afterwards, without recovering the earlier peaks. The flatness is the signal: it is not one class, it is all of them.',
      performance:
        'A clear three-phase shape. Steady mid 80s through November, a sharp drop through December to February bottoming near 68, and a partial recovery from March to the high 70s by June. The recovery began before any formal intervention.',
      behavior:
        'No conflict on record. Two entries note non-participation rather than disruption, both in the weeks straight after the transfer.',
    },
    extras: [
      {
        source: 'sis',
        kind: 'prior school record',
        date: '2025-09-03',
        title: 'Records received from prior school',
        body: 'Grade 10 final: Chemistry A-, US History B+, Precalculus A-. Attendance 96%. No behaviour record.',
      },
      {
        source: 'sis',
        kind: 'transfer enrollment',
        date: '2025-11-24',
        title: 'Transfer enrollment, grade 11',
        body: 'Mid-year transfer. Placed in Chemistry, US History, Precalculus, Spanish 3, PE. Course sequencing differs from prior school in Chemistry.',
      },
      {
        source: 'observation',
        kind: 'teacher observation',
        date: '2026-01-14',
        title: 'Second period',
        body: 'Sam has not volunteered an answer since he arrived. Work handed in is correct and complete. He eats lunch on the bench outside the library rather than in the hall.',
        author: 'Ms. Rivera',
      },
      {
        source: 'observation',
        kind: 'teacher observation',
        date: '2026-04-08',
        title: 'Second period',
        body: 'First unprompted contribution of the year, and it was a good one — he had spotted an error in the worked example on the board. Two students spoke to him afterwards.',
        author: 'Ms. Rivera',
      },
      {
        source: 'ai_tutor',
        kind: 'tutor session',
        date: '2026-01-08',
        title: 'Stoichiometry catch-up, 8:40pm',
        body: 'Asked for "everything I missed between the last school and this one" in chemistry. Worked through a self-made catch-up list over several sessions.',
        data: { hour: 20, minute: 40, turns: 38 },
      },
      {
        source: 'parent_input',
        kind: 'guardian note',
        date: '2025-12-15',
        title: 'About the move',
        body: 'We moved in November for my work, in the middle of the year, which I know is the worst timing. Sam has not said a word against it. He was at his last school from kindergarten. If he seems flat, that is what it is.',
        author: 'Kenji Nakamura',
      },
      {
        source: 'student_input',
        kind: 'student note',
        date: '2026-03-25',
        title: 'What I want you to know',
        body: 'I am not behind on the thinking, I am behind on the order things were taught in. A syllabus for the rest of the year would help more than extra time.',
        author: 'Sam Nakamura',
      },
      {
        source: 'document',
        kind: 'report card',
        date: '2026-01-23',
        title: 'Semester 1 report card',
        body: 'Chemistry C, US History C-. Teacher comment: "Transferred mid-semester; grade reflects a partial term. Capable of significantly more."',
      },
    ],
  },
  {
    id: 6,
    first_name: 'Priya',
    last_name: 'Raghunathan',
    grade: '11',
    pronouns: 'she/her',
    date_of_birth: '2009-09-09',
    guardians: [{ id: 307, name: 'Anjali Raghunathan', relationship: 'mother' }],
    subjects: [
      { name: 'AP Calculus — tests', kind: 'unit test', score: (m) => 96 + (m % 3) },
      { name: 'AP Calculus — homework', kind: 'homework', score: (m) => 44 + (m % 5) * 3 },
      { name: 'AP Physics — tests', kind: 'unit test', score: (m) => 94 + (m % 4) },
    ],
    absences_per_month: 1.0,
    behavior_per_month: 1.5,
    behavior_periods: [2, 3, 5],
    behavior_kinds: [
      'off task',
      'reading unrelated material',
      'did not start the task',
      'finished early, disengaged',
    ],
    engagement_by_period: [2.1, 1.9, 2.2, 2.0, 2.3, 4.8, 2.1],
    sections: {
      overview: {
        teacher_voice:
          'Priya sits at the top of every test and the bottom of every homework list. The gap is not carelessness — she can reproduce the whole method on demand and simply does not hand in practice she considers already learned. Sixth-period Studio Art is the one class she arrives early to.',
        guardian_voice:
          'Her mother says Priya reads university-level material for pleasure and describes the homework fight as the only friction at home. She asks whether there is anything harder available.',
        student_voice:
          'Priya says she does not see the point of twenty problems when she got the first two right. She says the art elective is "the only class where I do not already know what happens next".',
      },
      how_they_learn:
        'Priya learns extremely fast from first principles and disengages the moment a task becomes repetition. Her engagement is low and flat in every academic period and jumps to near the top of the scale in her sixth-period elective. She uses the AI tutor to go well beyond the syllabus rather than to catch up on it.',
      performance:
        'Two separate stories under one average. Test scores sit in the mid to high 90s all year, homework completion scores in the 40s and 50s. Any single grade that blends the two describes neither.',
      behavior:
        'Steady low-level off-task notes across academic periods, none involving conflict with staff or peers. The recurring word in the entries is "finished" rather than "refused".',
    },
    extras: [
      {
        source: 'sis',
        kind: 'enrollment',
        date: '2025-09-02',
        title: 'Enrolled, grade 11',
        body: 'Continuing student. Course load: AP Calculus, AP Physics, English 11, Spanish 3, Studio Art. Identified gifted, grade 4.',
      },
      {
        source: 'document',
        kind: 'gifted plan',
        date: '2025-09-24',
        title: 'Advanced learner plan',
        body: 'Eligible for subject acceleration and dual enrolment. Recommended: independent study option, reduced repetition on mastered standards. Plan not yet actioned this year.',
      },
      {
        source: 'observation',
        kind: 'teacher observation',
        date: '2025-10-15',
        title: 'Third period',
        body: 'Finished the problem set in nine minutes, correct, then read a library book for the remaining forty. Not disruptive. Declined the extension task because it was "the same but longer".',
        author: 'Mr. Halloran',
      },
      {
        source: 'observation',
        kind: 'teacher observation',
        date: '2026-04-29',
        title: 'Sixth period studio',
        body: 'Priya was in the studio fifteen minutes before the bell, again. She has been working on the same piece for three weeks and has redone the underdrawing twice by choice.',
        author: 'Ms. Okafor',
      },
      {
        source: 'ai_tutor',
        kind: 'tutor session',
        date: '2025-11-19',
        title: 'Beyond the syllabus, 7:20pm',
        body: 'Asked about Lagrangian mechanics and why the course "does the boring version first". Followed up with a question about variational principles.',
        data: { hour: 19, minute: 20, turns: 27 },
      },
      {
        source: 'ai_tutor',
        kind: 'tutor session',
        date: '2026-03-04',
        title: 'Beyond the syllabus, 8:55pm',
        body: 'Asked for a proof of the fundamental theorem of calculus "the way a mathematician would write it, not the textbook way".',
        data: { hour: 20, minute: 55, turns: 33 },
      },
      {
        source: 'parent_input',
        kind: 'guardian note',
        date: '2026-02-05',
        title: 'From home',
        body: 'The homework is the only argument in this house. She reads physics books for fun and will not do twenty practice problems. Is there anything harder she could be doing instead? We would rather she was stretched than negotiated with.',
        author: 'Anjali Raghunathan',
      },
      {
        source: 'student_input',
        kind: 'student note',
        date: '2026-03-16',
        title: 'What I want you to know',
        body: 'I will do the hard thing. I will not do the same thing twenty times. Ask me to prove it instead of asking me to practise it.',
        author: 'Priya Raghunathan',
      },
    ],
  },
];

// ---------------------------------------------------------------------------
// Filler students, so class rosters look real
// ---------------------------------------------------------------------------

const FILLER_NAMES: [string, string, string][] = [
  ['Nia', 'Carter', '11'],
  ['Tobias', 'Lindgren', '9'],
  ['Amara', 'Osei', '9'],
  ['Ruben', 'Delacroix', '10'],
  ['Hana', 'Suzuki', '10'],
  ['Eli', 'Bergstrom', '11'],
  ['Fatima', 'Haddad', '9'],
  ['Marcus', 'Bell', '10'],
  ['Ingrid', 'Solberg', '11'],
  ['Kwame', 'Mensah', '10'],
  ['Lucia', 'Ferrari', '9'],
  ['Owen', 'Blackwood', '11'],
  ['Zara', 'Nasser', '10'],
  ['Theo', 'Papadakis', '9'],
  ['Sadie', 'Kowalski', '11'],
  ['Andre', 'Moreau', '10'],
  ['Yuki', 'Tanaka', '9'],
  ['Rosa', 'Iglesias', '11'],
];

function fillerArc(
  id: number,
  first_name: string,
  last_name: string,
  grade: string,
): ArcSpec {
  const r = makeRng(id * 7919);
  const base = 68 + Math.floor(r() * 22);
  const slope = r() * 1.2 - 0.3;
  const them = `${first_name} ${last_name}`;
  return {
    id,
    first_name,
    last_name,
    grade,
    pronouns: 'they/them',
    date_of_birth: `${2011 - Number(grade) + 9}-0${1 + Math.floor(r() * 8)}-1${Math.floor(r() * 9)}`,
    guardians: [
      { id: 400 + id, name: `${pick(['Dana', 'Marco', 'Yvette', 'Samir'], r)} ${last_name}`, relationship: 'parent' },
    ],
    subjects: [
      { name: 'English', score: (m) => base + m * slope },
      { name: 'Mathematics', score: (m) => base + 4 + m * slope * 0.7 },
    ],
    absences_per_month: r() * 1.4,
    behavior_per_month: r() * 0.9,
    behavior_periods: [1 + Math.floor(r() * 7)],
    behavior_kinds: ['off task', 'late to class'],
    engagement_by_period: PERIODS.map(() => 2.6 + r() * 1.8),
    engagement_trend: r() * 0.2 - 0.1,
    sections: {
      overview: {
        teacher_voice: `${them} is a steady presence in class. Work comes in on time and the standard is consistent across the year, with no source showing a pattern that needs attention.`,
        guardian_voice: 'Home reports no concerns and asks to be told early if anything changes.',
        student_voice: `${first_name} says school is going fine and would like more notice before big assessments.`,
      },
      how_they_learn: `${them} works comfortably alone or in a pair, with no strong preference showing in the engagement samples. Attention is even across the timetable.`,
      performance: 'Scores sit in a narrow band across both subjects with a mild upward trend over the year.',
      behavior: 'Very little on record. Nothing recurring and nothing involving conflict.',
    },
    extras: [
      {
        source: 'sis',
        kind: 'enrollment',
        date: '2025-09-02',
        title: `Enrolled, grade ${grade}`,
        body: 'Continuing student. Full course load.',
      },
      {
        source: 'observation',
        kind: 'teacher observation',
        date: '2026-02-10',
        title: 'Class note',
        body: `${first_name} worked through the task without prompting and helped pack up afterwards.`,
        author: 'Ms. Rivera',
      },
      {
        source: 'parent_input',
        kind: 'guardian note',
        date: '2026-01-19',
        title: 'From home',
        body: 'No concerns from our side. Please let us know early if there are any.',
      },
      {
        source: 'student_input',
        kind: 'student note',
        date: '2026-03-06',
        title: 'What I want you to know',
        body: 'I would rather have the deadline early than be reminded about it later.',
      },
    ],
  };
}

const ARCS: ArcSpec[] = [
  ...HERO_ARCS,
  ...FILLER_NAMES.map(([f, l, g], i) => fillerArc(7 + i, f, l, g)),
];

export const HERO_STUDENT_IDS = HERO_ARCS.map((a) => a.id);

// ---------------------------------------------------------------------------
// Record generation
// ---------------------------------------------------------------------------

let nextRecordId = 1000;

function makeRecord(
  studentId: number,
  fields: Omit<StudentRecord, 'id' | 'student' | 'created_at' | 'data' | 'author'> &
    Partial<Pick<StudentRecord, 'data' | 'author'>>,
): StudentRecord {
  return {
    id: nextRecordId++,
    student: studentId,
    data: {},
    author: null,
    created_at: `${fields.date}T17:00:00Z`,
    ...fields,
  };
}

function generateRecords(arc: ArcSpec): StudentRecord[] {
  const r = makeRng(arc.id * 104_729 + 17);
  const out: StudentRecord[] = [];
  const assessmentDates: string[] = [];

  // Assessments: one per subject per month.
  arc.subjects.forEach((subject, si) => {
    for (let m = 0; m < MONTH_LABELS.length; m++) {
      const days = daysByMonth[m];
      const date = days[Math.min(days.length - 1, 6 + si * 4 + Math.floor(r() * 4))];
      const kind = subject.kind ?? ROTATING_KINDS[(m + si) % ROTATING_KINDS.length];
      const swing =
        arc.format_swing && !subject.kind
          ? kind === 'project'
            ? arc.format_swing
            : kind === 'timed test'
              ? -arc.format_swing
              : 0
          : 0;
      const score = clamp(
        Math.round(subject.score(m) + swing + (r() * 4 - 2)),
        20,
        100,
      );
      assessmentDates.push(date);
      out.push(
        makeRecord(arc.id, {
          source: 'assessment',
          kind,
          date,
          title: `${subject.name} — ${kind}`,
          body: `Scored ${score} out of 100 on the ${MONTH_LABELS[m]} ${kind}.`,
          data: { subject: subject.name, score, max: 100 },
        }),
      );
    }
  });

  // Attendance: absences, with an optional Monday weighting.
  for (let m = 0; m < MONTH_LABELS.length; m++) {
    const days = daysByMonth[m];
    const count = Math.round(arc.absences_per_month + (r() * 1.2 - 0.6));
    for (let i = 0; i < count; i++) {
      const mondays = days.filter((d) => weekdayOf(d) === 'Monday');
      const useMonday = arc.monday_bias != null && r() < arc.monday_bias;
      const date = useMonday ? pick(mondays, r) : pick(days, r);
      const tardy = !useMonday && r() < 0.3;
      out.push(
        makeRecord(arc.id, {
          source: 'attendance',
          kind: tardy ? 'tardy' : 'absence',
          date,
          title: tardy ? 'Late to first period' : 'Absent, full day',
          body: tardy ? 'Arrived 22 minutes into first period.' : 'No contact from home before the bell.',
          data: { status: tardy ? 'tardy' : 'absent', minutes_late: tardy ? 22 : 0 },
        }),
      );
    }
  }

  // Health-office visits the school day before an assessment.
  if (arc.nurse_before_assessment) {
    for (const date of assessmentDates) {
      if (r() >= arc.nurse_before_assessment) continue;
      const m = monthOf(date);
      const days = daysByMonth[m];
      const idx = days.indexOf(date);
      if (idx <= 0) continue;
      out.push(
        makeRecord(arc.id, {
          source: 'attendance',
          kind: 'health office visit',
          date: days[idx - 1],
          title: 'Health office — stomach ache',
          body: 'Rested 20 minutes, no temperature, returned to class.',
          data: { status: 'present', minutes_out: 20 },
        }),
      );
    }
  }

  // Behaviour incidents, clustered in the arc's periods.
  for (let m = 0; m < MONTH_LABELS.length; m++) {
    const days = daysByMonth[m];
    const count = Math.round(arc.behavior_per_month + (r() * 1.0 - 0.5));
    for (let i = 0; i < count; i++) {
      const period = pick(arc.behavior_periods, r);
      const kind = pick(arc.behavior_kinds, r);
      out.push(
        makeRecord(arc.id, {
          source: 'behavior',
          kind,
          date: pick(days, r),
          title: `Period ${period} — ${kind}`,
          body: `Logged in period ${period}. Redirected once; no further action taken.`,
          data: { period, severity: 1 + Math.floor(r() * 2) },
        }),
      );
    }
  }

  // Engagement samples: one per period per month.
  for (let m = 0; m < MONTH_LABELS.length; m++) {
    const days = daysByMonth[m];
    // Iterate the arc's own curve, not the chart's PERIODS constant: a display
    // constant must not decide what data exists, or widening it yields NaN.
    for (let period = 1; period <= arc.engagement_by_period.length; period++) {
      const step = arc.engagement_step && m >= arc.engagement_step.month ? arc.engagement_step.delta : 0;
      const mean =
        arc.engagement_by_period[period - 1] + (arc.engagement_trend ?? 0) * m + step;
      const rating = clamp(Math.round(mean + (r() * 1.0 - 0.5)), 1, 5);
      out.push(
        makeRecord(arc.id, {
          source: 'engagement',
          kind: 'observation sample',
          date: pick(days, r),
          title: `Period ${period} — engagement ${rating} of 5`,
          body: '',
          data: { period, rating },
        }),
      );
    }
  }

  // Authored one-off records.
  for (const extra of arc.extras) {
    out.push(
      makeRecord(arc.id, {
        source: extra.source,
        kind: extra.kind,
        date: extra.date,
        title: extra.title,
        body: extra.body,
        data: extra.data ?? {},
        author: extra.author ?? null,
      }),
    );
  }

  // Newest first, matching `StudentRecord.Meta.ordering`.
  return out.sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : b.id - a.id));
}

// ---------------------------------------------------------------------------
// Assembled fixtures
// ---------------------------------------------------------------------------

function toStudent(arc: ArcSpec): Student {
  return {
    id: arc.id,
    first_name: arc.first_name,
    last_name: arc.last_name,
    name: `${arc.first_name} ${arc.last_name}`,
    grade: arc.grade,
    date_of_birth: arc.date_of_birth,
    pronouns: arc.pronouns,
  };
}

export const students: Student[] = ARCS.map(toStudent);

const recordsByStudent = new Map<number, StudentRecord[]>(
  ARCS.map((arc) => [arc.id, generateRecords(arc)]),
);

const arcsById = new Map(ARCS.map((arc) => [arc.id, arc]));

function studentIds(...ids: number[]): Student[] {
  return ids.map((id) => students.find((s) => s.id === id)!).filter(Boolean);
}

export const classrooms: Classroom[] = [
  {
    id: 1,
    name: 'Algebra I — Section B',
    subject: 'Mathematics',
    grade: '9',
    period: '4',
    teachers: ['Ms. Rivera'],
    students: studentIds(2, 3, 8, 9, 13, 17, 20, 24),
  },
  {
    id: 2,
    name: 'AP Biology',
    subject: 'Science',
    grade: '10',
    period: '2',
    teachers: ['Ms. Rivera'],
    students: studentIds(1, 4, 10, 11, 14, 19, 22),
  },
  {
    id: 3,
    name: 'Chemistry',
    subject: 'Science',
    grade: '11',
    period: '2',
    teachers: ['Ms. Rivera'],
    students: studentIds(5, 6, 7, 12, 15, 18, 21),
  },
  {
    id: 4,
    name: 'English 9',
    subject: 'English',
    grade: '9',
    period: '1',
    teachers: ['Mr. Halloran'],
    students: studentIds(2, 3, 8, 9, 13, 17, 20, 24),
  },
  {
    id: 5,
    name: 'World History',
    subject: 'History',
    grade: '',
    period: '3',
    teachers: ['Mr. Halloran'],
    students: studentIds(4, 5, 10, 11, 15, 16, 21, 23),
  },
  {
    id: 6,
    name: 'Studio Art',
    subject: 'Arts',
    grade: '',
    period: '6',
    teachers: ['Ms. Okafor'],
    students: studentIds(6, 4, 14, 16, 19, 23),
  },
];

interface MockAccount {
  password: string;
  me: Me;
}

function guardianAccount(
  id: number,
  username: string,
  first: string,
  last: string,
  wardIds: number[],
): [string, MockAccount] {
  return [
    username,
    {
      password: 'demo12345',
      me: {
        id,
        username,
        first_name: first,
        last_name: last,
        role: 'guardian',
        student_id: null,
        students: studentIds(...wardIds),
      },
    },
  ];
}

function studentAccount(
  id: number,
  username: string,
  studentId: number,
): [string, MockAccount] {
  const student = students.find((s) => s.id === studentId)!;
  return [
    username,
    {
      password: 'demo12345',
      me: {
        id,
        username,
        first_name: student.first_name,
        last_name: student.last_name,
        role: 'student',
        student_id: studentId,
        students: [student],
      },
    },
  ];
}

/** Classroom ids each teacher account teaches, keyed by username. */
const taughtByUsername = new Map<string, number[]>();

function teacherAccount(
  id: number,
  username: string,
  first: string,
  last: string,
  display: string,
): [string, MockAccount] {
  const taught = classrooms.filter((c) => c.teachers.includes(display));
  taughtByUsername.set(username, taught.map((c) => c.id));
  const roster = new Map<number, Student>();
  for (const c of taught) for (const s of c.students) roster.set(s.id, s);
  return [
    username,
    {
      password: 'demo12345',
      me: {
        id,
        username,
        first_name: first,
        last_name: last,
        role: 'teacher',
        student_id: null,
        students: [...roster.values()],
      },
    },
  ];
}

const accounts = new Map<string, MockAccount>([
  // Usernames match the seeded accounts so the same demo logins work whether
  // fixtures or the real API are in play.
  teacherAccount(101, 't.elena.ramirez', 'Elena', 'Ramirez', 'Ms. Rivera'),
  teacherAccount(102, 'm.halloran', 'Dermot', 'Halloran', 'Mr. Halloran'),
  guardianAccount(201, 'g.rosa.delgado', 'Rosa', 'Delgado', [2, 7]),
  guardianAccount(202, 'e.whitaker', 'Erin', 'Whitaker', [4]),
  studentAccount(11, 's.maya.okonkwo', 1),
  studentAccount(14, 's.whitaker', 4),
]);

/** Shown on the login form so a demo audience can sign in. */
export const DEMO_LOGINS: { username: string; role: Role; note: string }[] = [
  // These must match the seeded accounts in passport/seed/, or the one-click
  // demo logins fail against the real API.
  { username: 't.elena.ramirez', role: 'teacher', note: 'Two classrooms, 21 students' },
  { username: 'g.rosa.delgado', role: 'guardian', note: 'Fatima Haddad and Talia Mensah' },
  { username: 's.maya.okonkwo', role: 'student', note: 'Their own passport' },
];

export const DEMO_PASSWORD = 'demo12345';

/** Classrooms the given user may see. */
export function classroomsFor(me: Me): Classroom[] {
  if (me.role === 'teacher') {
    const taught = new Set(taughtByUsername.get(me.username) ?? []);
    return classrooms.filter((c) => taught.has(c.id));
  }
  const visible = new Set(me.students.map((s) => s.id));
  return classrooms.filter((c) => c.students.some((s) => visible.has(s.id)));
}

export function authenticate(username: string, password: string): Me | null {
  const account = accounts.get(username.trim().toLowerCase());
  if (!account || account.password !== password) return null;
  return account.me;
}

export function recordsFor(studentId: number): StudentRecord[] {
  return recordsByStudent.get(studentId) ?? [];
}

export function passportFor(studentId: number): Passport | null {
  const arc = arcsById.get(studentId);
  if (!arc) return null;
  const records = recordsFor(studentId);
  return {
    student: toStudent(arc),
    guardians: arc.guardians,
    sections: arc.sections,
    generated_at: '2026-06-05T09:00:00Z',
    record_count: records.length,
    records,
  };
}

/** Append a record written during the session, so the UI updates in place. */
export function addRecord(
  studentId: number,
  fields: Omit<StudentRecord, 'id' | 'student' | 'created_at'>,
): StudentRecord {
  const record = makeRecord(studentId, fields);
  record.created_at = new Date().toISOString();
  recordsByStudent.set(studentId, [record, ...recordsFor(studentId)]);
  return record;
}

// ---------------------------------------------------------------------------
// Mocked question answering
// ---------------------------------------------------------------------------

function numberData(record: StudentRecord, key: string): number | null {
  const value = record.data[key];
  return typeof value === 'number' ? value : null;
}

/**
 * Stands in for the Bedrock call behind `POST /api/students/<id>/ask/`.
 * It reads the same records the real prompt would, so the shape of the answer
 * and its citations match what the API will return.
 */
export function answerFor(studentId: number, question: string): Answer {
  const arc = arcsById.get(studentId);
  const records = recordsFor(studentId);
  const name = arc ? arc.first_name : 'This student';
  const q = question.toLowerCase();

  let cited: StudentRecord[];
  let answer: string;

  if (/engag|attention|focus|period|when/.test(q)) {
    cited = records.filter((r) => r.source === 'engagement');
    const byPeriod = new Map<number, number[]>();
    for (const r of cited) {
      const period = numberData(r, 'period');
      const rating = numberData(r, 'rating');
      if (period == null || rating == null) continue;
      byPeriod.set(period, [...(byPeriod.get(period) ?? []), rating]);
    }
    const means = [...byPeriod.entries()]
      .map(([period, xs]) => ({ period, mean: xs.reduce((a, b) => a + b, 0) / xs.length }))
      .sort((a, b) => b.mean - a.mean);
    const best = means[0];
    const worst = means[means.length - 1];
    answer =
      `${name} is most engaged in period ${best.period}, averaging ${best.mean.toFixed(1)} out of 5 across ${cited.length} samples, ` +
      `and least engaged in period ${worst.period} at ${worst.mean.toFixed(1)}. ` +
      `The gap of ${(best.mean - worst.mean).toFixed(1)} points is wide enough to be about the shape of the day rather than sampling noise. ` +
      `Where you have a choice, put demanding work in period ${best.period}.`;
    cited = cited.slice(0, 6);
  } else if (/score|grade|perform|assess|test|progress/.test(q)) {
    cited = records.filter((r) => r.source === 'assessment');
    const bySubject = new Map<string, StudentRecord[]>();
    for (const r of cited) {
      const subject = typeof r.data.subject === 'string' ? r.data.subject : 'Unknown';
      bySubject.set(subject, [...(bySubject.get(subject) ?? []), r]);
    }
    const lines = [...bySubject.entries()].map(([subject, rs]) => {
      const ordered = [...rs].sort((a, b) => (a.date < b.date ? -1 : 1));
      const first = numberData(ordered[0], 'score') ?? 0;
      const last = numberData(ordered[ordered.length - 1], 'score') ?? 0;
      const delta = last - first;
      const direction = delta > 4 ? 'up' : delta < -4 ? 'down' : 'level';
      return `${subject} is ${direction} (${first} in September, ${last} in June)`;
    });
    answer = `Across ${cited.length} assessments: ${lines.join('; ')}. ${arc?.sections.performance ?? ''}`;
    cited = cited.slice(0, 6);
  } else if (/behav|incident|referral|discipline/.test(q)) {
    cited = records.filter((r) => r.source === 'behavior');
    const byPeriod = new Map<number, number>();
    for (const r of cited) {
      const period = numberData(r, 'period');
      if (period != null) byPeriod.set(period, (byPeriod.get(period) ?? 0) + 1);
    }
    const top = [...byPeriod.entries()].sort((a, b) => b[1] - a[1])[0];
    answer = top
      ? `There are ${cited.length} behaviour entries on file. The largest cluster is period ${top[0]} with ${top[1]} of them. ${arc?.sections.behavior ?? ''}`
      : `There are no behaviour entries on file for ${name}.`;
    cited = cited.slice(0, 6);
  } else if (/attend|absent|absence|late|miss/.test(q)) {
    cited = records.filter((r) => r.source === 'attendance');
    const byWeekday = new Map<string, number>();
    for (const r of cited.filter((r) => r.data.status === 'absent')) {
      const day = weekdayOf(r.date);
      byWeekday.set(day, (byWeekday.get(day) ?? 0) + 1);
    }
    const top = [...byWeekday.entries()].sort((a, b) => b[1] - a[1])[0];
    answer = top
      ? `${cited.length} attendance entries, of which ${[...byWeekday.values()].reduce((a, b) => a + b, 0)} are full-day absences. ${top[0]} accounts for ${top[1]} of them, more than any other weekday.`
      : `No absences are recorded for ${name}.`;
    cited = cited.slice(0, 6);
  } else {
    cited = records.filter((r) =>
      ['observation', 'parent_input', 'student_input', 'document'].includes(r.source),
    );
    answer =
      `${arc?.sections.overview.teacher_voice ?? ''} ` +
      `${arc?.sections.how_they_learn ?? ''} ` +
      `This draws on ${records.length} records across ${new Set(records.map((r) => r.source)).size} sources.`;
    cited = cited.slice(0, 5);
  }

  const record = addRecord(studentId, {
    source: 'question',
    kind: 'asked question',
    date: new Date().toISOString().slice(0, 10),
    title: question.slice(0, 200),
    body: answer,
    data: { cited_record_ids: cited.map((r) => r.id) },
    author: null,
  });

  return {
    record,
    question,
    answer: answer.trim(),
    cited_record_ids: cited.map((r) => r.id),
  };
}
