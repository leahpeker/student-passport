# Handoff: Teacher view — class tabs, roster, student passport

## Overview

The teacher-facing surface of Student Passport (`leahpeker/student-passport`, branch `main`). One screen: class tabs across the top, a class roster down the left, and the selected student's passport filling the rest. The passport has two tabs — **Insights** (default) and **Records** — because the product's premise is that the whole student, not the transcript, is what a new teacher needs first.

Backend models exist (`passport/models.py`, phase 1 complete). No frontend exists yet, so this is a greenfield implementation of phases 4–5 in `docs/spec.md`.

## About the design files

`reference/Teacher View.dc.html` is a **design reference created in HTML** — a prototype showing intended look, copy and behavior. It is not production code to copy. It is a self-contained streaming-component file (a `<x-dc>` template plus a logic class in a `<script type="text/x-dc">` tag) with all values inline. Open it in a browser to interact with it.

The task is to **recreate this design in the repo's chosen environment**: React + Vite + TypeScript + Tailwind, with Recharts for charts, as `docs/spec.md` specifies. Follow that stack's conventions; do not port the DC runtime, `support.js`, or the inline-style approach.

`reference/_ds/nocturne-…/styles.css` is the design system's token sheet. Take colors, spacing, radii and shadows from it (or transcribe the tokens below into your Tailwind theme). Its class names (`.btn`, `.card`, `.tag`, `.input`, `.table`) are the component vocabulary the mockup uses.

## Fidelity

**High-fidelity.** Colors, typography, spacing, copy and interaction states are final. Recreate pixel-perfectly using the codebase's libraries. The one exception: all student data is synthetic sample data authored for the mockup — replace it with API data (see *Data mapping*).

## Screens / views

### 1. App shell

- **Root**: fixed design width 1440px, min-height 1020px, `background #161826`, column flex.
- **Header**: 14px 28px padding, `background linear-gradient(180deg,#1b1d2c,#161826)`, row flex, `gap 16.8px`, `align-items center`.
  - Brand: 22×22px rounded-6px box, `1px solid #9184d9`, letter "P" 11px `#9184d9`; label "Student Passport" 16px/500, `letter-spacing -0.01em`. `margin-right:auto` on the group.
  - Role nav: "Teacher" (active, `#9184d9`), "Guardian", "Student" — 13px, inactive `color-mix(in srgb,#e9e9ed 62%,transparent)`, `gap 18px`. Maps to the three views in the README; teacher is the only one in scope here.
  - 1px × 20px vertical divider at `color-mix(in srgb,#e9e9ed 14%,transparent)`.
  - User: "R. Alvarez" 13px at 70% text, then a 26px circle avatar `background #2b2741`, `color #d2cefd`, initials 11px.

### 2. Class tabs

- Row, `padding 0 28px`, `align-items flex-end`, `gap 2px`. Bottom rule is a **fading** 1px gradient (Nocturne's signature): `linear-gradient(to right, transparent, color-mix(in srgb,#e9e9ed 14%,transparent) 48px, color-mix(in srgb,#e9e9ed 14%,transparent) calc(100% - 48px), transparent) no-repeat bottom / 100% 1px`.
- Each tab is a button, column flex, `gap 2px`, `padding 11px 16px 10px`, `border-radius 8px 8px 0 0`, `border-bottom 2px solid transparent`.
  - Line 1: class name, 13.5px/500. Line 2: "Period {n} · {count} students", 11.5px at 48% text.
  - **Active**: `border-bottom-color #9184d9`, `background linear-gradient(180deg,rgba(145,132,217,0.10),transparent)`, full-strength text.
  - **Inactive**: text at 62%.
- Right end, `margin-left:auto`, `padding-bottom 8px`: "Spring 2026 · {N} classes · {M} students", 11.5px at 42%.
- Sample classes: Biology 9A (P2, 8), Biology 9B (P3, 6), Bio Lab 9 (P5, 7), Advisory 9 (P7, 5). A student may appear in several classes.

### 3. Roster (left column)

- Grid `300px 1fr` for roster + passport; roster `align-self stretch`, `padding 16.8px`, `border-right 1px solid color-mix(in srgb,#e9e9ed 10%,transparent)`, column flex `gap 11.2px`.
- Header row: kicker "ROSTER" (10px, `letter-spacing 0.1em`, uppercase, `#9184d9`) and "{n} students" 11px at 45%, space-between.
- Search: `.input` with `min-height 32px`, `font-size 13px`, placeholder "Search students". (Non-functional in the mock; wire it to filter the roster client-side.)
- Student rows: button, row flex, `gap 9px`, `padding 8px 9px`, `border-radius 8px`.
  - 28px circle avatar, initials 11px. Selected: `background #2b2741`, `color #d2cefd`. Unselected: `background #232532`, text at 60%.
  - Name 13.5px with ellipsis overflow; meta line "{recordCount} records · {attendanceRate}" 11px at 45%.
  - **Selected row**: `background #232532`, `box-shadow inset 2px 0 0 #9184d9`.
  - Signal dots, right, 6px circles, `gap 3px`, each with a `title`:
    - `#3f424d` "Passport thin" when `recordCount < 40`
    - `#5d5294` "Plan on file" when the student has an IEP/504 tag
    - `#968ae0` "New observation this week" when `recordCount >= 40`
- Legend pinned to the bottom (`margin-top auto`, `padding-top 16.8px`), 11px at 40%, `gap 5.6px`: "New observation this week", "Plan on file (IEP / 504)", "Passport thin — under 40 records", each with its matching 6px dot.

### 4. Passport header (both tabs)

- Row flex, `gap 16.8px`, `align-items flex-start`, inside `main` (`padding 22.4px 28px 44px`, column flex, `gap 22.4px`).
- 54px circle avatar, initials 19px, `background #2b2741`, `color #d2cefd`.
- Name `h1` 26px/500, `letter-spacing -0.02em`; beside it 12.5px at 55%: "Grade 9 · b. 2011 · Passport since Sep 2025".
- Tag row: `.tag .tag-neutral` chips (grade, plans, guardian context, "{n} voices on file").
- Summary paragraph, `max-width 760px`, 13.5px/1.6 at 78%, `text-wrap pretty`.
- Right column, right-aligned: `.btn.btn-secondary` "Export JSON" + `.btn.btn-primary` "Ask the passport"; below, 11px at 40%: "Narrative generated {relative time} · {recordCount} records".
- Below the header: the fading 1px divider (same gradient as the tab rule, at 16% instead of 14%).

### 5. Passport tab bar

- Row, `gap 5.6px`. Each tab a button, `padding 11.2px 14px`, `border-radius 8px`, `align-items baseline`, `gap 7px`: label 13px/500 plus a note 11px at 42%.
  - "Insights" — note "the student as a whole"
  - "Records" — note "{recordCount} structured entries"
  - **Active**: `background #2b2741`, `box-shadow inset 0 0 0 1px #5d5294`, full text. **Inactive**: transparent, `inset 0 0 0 1px color-mix(in srgb,#e9e9ed 12%,transparent)`, text at 62%.

### 6. Insights tab (the landing view)

Deliberately short above the fold: a brief, a quote, three voices, then four collapsed rows.

**a. "Before your next lesson with {first}" card** — grid `1.35fr 1fr` with the quote card.
- `padding 19px`, `border-radius 14px`, `background radial-gradient(120% 140% at 6% 0%,#221f36 0%,#1b1d2c 66%)`, `box-shadow inset 0 0 0 1px #423a6a`.
- Kicker 10px, `letter-spacing 0.12em`, uppercase, `#b5abfc`.
- Three items, each `padding-left 11.2px`, `border-left 2px solid #796cbf`: label 11px uppercase at 48%, text 14px/1.55.
  - "When to teach them" — derived: highest and lowest engagement period with ratings out of 5.
  - "What works" — derived: strongest learning format and the one to avoid.
  - "What is going on" — derived: top stressor label + text.
  - Thin passports show a single item, "Start here", telling the teacher one observation is the most useful thing they could add.

**b. "In their own words" card** — `padding 19px`, `border-radius 14px`, `background #232532`; kicker 10px uppercase at 45%; the student's own note at 15px/1.6 in quotes; attribution 12px at 50%. Hidden when the student has no input on file.

**c. Overview** — `h2` "Overview" 18px/500 with a 12.5px at 50% subhead: "The same student, described by the three people who know different parts of {first}." Three equal `.card`s (`gap 8.4px`, `padding 16.8px`):
- "What their teachers see" / "What home sees" / "What they say themselves"
- Each: title 14.5px/500, provenance line 10.5px uppercase `letter-spacing 0.06em` at 40% ("teacher observations · {first}", "guardian input · {name}", "student input · {name}"), body 13px/1.65 at 80%.
- If no voices exist: a single dashed panel (`1px dashed color-mix(in srgb,#e9e9ed 18%,transparent)`, radius 8px) explaining that nobody has written anything yet.

**d. Four collapsible panels**, in order. Header is a full-width button: `padding 11.2px 14px`, `border-radius 8px`, `box-shadow inset 0 0 0 1px color-mix(in srgb,#e9e9ed 12%,transparent)`; label 15px/500, note 12px at 45%, and a `+` / `–` mark 15px `#9184d9` at `margin-left:auto`. Open headers also take `background #232532`. All start closed.

1. **Engagement and behaviour** — "rating by period, and what precedes each behaviour entry". Grid `1.15fr 1fr`:
   - *Engagement by period* card: seven horizontal bars (Period 1–4, Lunch, Period 6, Period 7), each `height 22px`, `border-radius 0 4px 4px 0`, width `rating/5`, printed value beside it (12px at 65%). Peak bar `#968ae0`, lowest `#3a3455`, others `#5d5294`. Caption 11px at 38%: "Average engagement rating by period, out of 5. Highest {peak}, lowest {low}, from 70 samples across the year." Then the narrative read, 13px/1.65 at 80%.
   - Thin passports replace the chart with a dashed "Nothing recorded" panel and a `.btn.btn-secondary` "Log a check-in" — never invented values.
   - *Behaviour, in context* card: note line 12px at 55% ("{N} behaviour entries on record." / "1 behaviour entry on record." / "No behaviour entries on record." + the attendance pattern sentence), then entries: 52px date column 11px at 42%, a kind chip, title 12.5px, note 11.5px/1.5 at 58%.
2. **In the room, and outside school** — "observations, tutor questions, stressors, how they work best". Intro line 13px/1.6 at 65%. Grid `1.25fr 1fr`:
   - *Engagement across the day*: 7 rows × 6 weeks heatmap, 20px cells, `border-radius 3px`, `gap 3px`, cell fill `color-mix(in srgb,#968ae0 {value}%,#1d1f2c)`; row labels 10.5px at 48%, column labels W1–W6 10px at 35%; a legend bar `linear-gradient(to right,#232532,#3a3455,#5d5294,#968ae0)` labelled "Disengaged"/"Locked in"; narrative read below.
   - *What they ask the AI tutor*: count chip (`background #2b2741`, `color #d2cefd`, min-width 26px) + theme 12.5px + a quoted example 11.5px at 52%; footer note 11px at 38%.
   - Then a 3-up grid: *Classroom situations* (each item `padding-left 9px`, `border-left 2px solid #5d5294`, timestamp 11px at 42%, text 12.5px/1.55), *Stressors outside school* (`.tag.tag-accent` label + provenance 11px at 40% + text 12.5px at 78%; footer: "Visible to teachers and counselors. Not exported to another school without review."), *How they interact with learning* (four labelled 4px progress bars — `#968ae0` above 70, `#5d5294` 41–70, `#3f424d` at or below 40 — plus a read).
   - Footer strip: `1px solid color-mix(in srgb,#9184d9 35%,transparent)`, radius 8px, prompt text + `.btn.btn-primary` "Add an observation".
   - Thin passports: a single dashed accent panel, kicker "Nothing written down yet", the gap explanation, and two buttons ("Add the first observation", "Ask the class team").
3. **Plans and written notes** — "IEP, 504, counselor and teacher prose". 3-up `.card` grid: source chip, date 11px at 42%, title 14px/500, excerpt 12.5px/1.6 at 72%, owner + extract meta 11px at 38%. Source is any document whose title matches IEP / 504 / plan / notes / monitoring / check-in / progress.
4. **Guardian input, student input and questions** — grid `1fr 1fr`.
   - Left: heading + explainer ("Nothing here comes from a system; it was written by a guardian."), the guardian note card (title, `.tag.tag-neutral` "Guardian input", date, body 13px/1.65 at 82%, "— {name}"), then **Add a note from home**: `.field` label "Title (optional)" + `.input`; `.field` label "What would you like the next teacher to know?" + 4-row textarea; `.btn.btn-primary` "Add to the passport".
   - Right: heading + "What {first} has asked to be passed on. This is the only section the student writes.", the student note card, then **Ask about this student**: explainer, `.field` label "Your question" + `.input`, four `.tag.tag-outline` suggested questions ("When is this student most engaged?", "How has their performance moved this year?", "Is there a pattern in the behaviour entries?", "What should I know before their first lesson with me?"), `.btn.btn-primary` "Ask" + "Speech-to-text available" 11px at 38%, then the last answer in a `#1d1f2c` block: question 12.5px `#d2cefd`, answer 12.5px/1.65 at 80%, footer "Answered from {n} records. Saved to the passport."

### 7. Records tab

- **Structured** section: kicker "Structured" (10px uppercase `#9184d9`), `h2` "Scores, attendance and behavior entries", provenance line "sis · assessment · attendance · behavior" 12px at 48%. Grid `1.05fr 1fr 1.15fr`:
  - *Assessment*: headline percentile 28px/500 + note 12px at 55%; an SVG trend line (`stroke #9184d9`, 1.5px) over a dashed cohort line (`color-mix(in srgb,#e9e9ed 22%,transparent)`, `stroke-dasharray 3 3`) with an endpoint dot; axis labels "Fall benchmark / Winter / Spring interim" 10.5px at 40%; then per-subject rows — 96px label at 60%, 4px track `color-mix(in srgb,#e9e9ed 10%,transparent)` with `#796cbf` fill, value right-aligned in 52px.
  - *Attendance*: headline rate 28px + absence note; five vertical weekday bars, `height` = pct × 0.62, `border-radius 3px 3px 0 0`, `#968ae0` when below 70% else `color-mix(in srgb,#e9e9ed 20%,transparent)`, labels 10.5px at 45%; pattern sentence 12px/1.55 at 60%.
  - *Behavior records*: four counters (20px/500 numbers over 10.5px at 48% labels — Suspensions, Expulsions, Detentions, Referrals), then entries with a 52px date column, a kind chip, title 12.5px and note 11.5px at 55%; rows separated by `border-top 1px solid color-mix(in srgb,#e9e9ed 8%,transparent)`.
  - Kind chip colors: Suspension `#5c2b33`/`#f6e3e6`; Detention & Referral `#423a6a`/`#e7e5fe`; Commendation `#2b3a33`/`#dbeee4`; Note `#292b31`/`#e5e6ea`. 10px, `padding 2px 7px`, radius 6px.
- **Unstructured** section: kicker "Unstructured", `h2` "Every source document on file", provenance "document · parent_input · student_input". 2-up `.card`s: source chip + date + owner (right), title 14.5px/500, excerpt 12.5px/1.6 at 70%, then "Open source file" 11.5px `#9184d9` + extract meta 11px at 35%.
  - Source chip colors: "Google Docs" `#2b2741`/`#d2cefd`; "Google Sheets" `#243329`/`#d6ecdd`; "PDF · SIS" `#292b31`/`#d7d9df`.
  - Thin passports append a dashed "Nothing else on file" panel with `.btn.btn-secondary` "Request records" and `.btn.btn-ghost` "Add a note".

## Interactions & behavior

- **Class tab click** — switches roster. If the currently selected student is also in the new class, selection persists; otherwise the first student in the new roster is selected.
- **Roster row click** — loads that student's passport. Passport tab and panel open/closed state persist across student switches in the mock; consider resetting panels to closed on student change if that reads better in use.
- **Passport tab click** — Insights ⇄ Records, mutually exclusive; no content from one renders in the other.
- **Panel header click** — toggles that panel only; `+` becomes `–`; other panels unaffected. All closed on first load.
- **Search, both forms, Ask, Export JSON, Add an observation** — inert in the mock. Real behavior: search filters the roster; the two forms POST to `/api/students/<id>/input/`; Ask POSTs `/api/students/<id>/ask/` and appends the exchange (spec: the exchange is written back as a `question` record); Export hits `/api/students/<id>/export/`.
- **Empty/thin states are load-bearing.** Where a student genuinely has no data, show the named gap state and an action — never a chart with placeholder numbers. Three of the twelve sample students exist to demonstrate this (18, 22 and 34 records).
- **States**: every interactive element takes a hover tint and pressed state from the accent ramp, and `:focus-visible { outline: 2px solid var(--color-accent); outline-offset: 2px; }`. The design system's stylesheet already provides these for `.btn`, `.input`, `.tag`, `.table`; match them for the custom tabs, roster rows and panel headers.
- **No responsive spec.** The mock is a fixed 1440px desktop canvas. Agree breakpoints separately; the roster is the obvious first thing to collapse.

## State management

```
classId: string            // active class tab
studentId: string          // selected roster student
passportTab: 'insights' | 'records'
openPanels: Record<'learn'|'room'|'plans'|'home', boolean>   // all false initially
```

Data fetching (per `docs/spec.md`):
- `GET /api/me/` — role gate; teacher only for this screen.
- `GET /api/classrooms/` — class tabs and rosters.
- `GET /api/students/<id>/passport/` — the narrative sections behind Insights (`?refresh=1` regenerates). The header's "Narrative generated {time} · {n} records" comes from `generated_at` and `record_count`; if `record_count` is behind the live count, the narrative is stale — surface that.
- `GET /api/students/<id>/records/` — everything else, filterable by `source`.
- `POST /api/students/<id>/ask/`, `POST /api/students/<id>/input/`, `GET /api/students/<id>/export/`.

## Data mapping

The mock's per-student object maps onto `StudentRecord.source` as follows:

| UI element | Source(s) |
| --- | --- |
| Brief "When to teach them", engagement chart, heatmap | `observation`, `ai_tutor` (`data` engagement ratings) |
| Brief "What works", "How they interact with learning" | `observation` |
| Brief "What is going on", "Stressors outside school" | `observation`, `parent_input` |
| "In their own words" | `student_input` |
| Overview — teachers / home / student | `observation` / `parent_input` / `student_input` |
| Behaviour in context, behavior counters | `behavior` |
| Classroom situations | `observation` |
| What they ask the AI tutor | `ai_tutor` |
| Plans and written notes, source documents | `document` |
| Assessment card | `assessment` (`data` scores) |
| Attendance card | `attendance` (`data` counts) |
| Header tags, subhead | `Student`, `sis` |
| Ask answer block | `question` |

Records with numbers live in `data`; prose lives in `body` — the Insights tab is mostly `body`, the Records tab mostly `data`. Every derived line in the brief is computed from those records, not authored: keep it that way so the brief can't drift from the evidence.

## Design tokens

From `reference/_ds/nocturne-…/styles.css` (`:root`). Use the variables, not the literals, wherever you can.

**Roles** — `--color-bg #161826`, `--color-surface #232532`, `--color-text #e9e9ed`, `--color-accent #9184d9`, `--color-divider color-mix(in srgb,#e9e9ed 16%,transparent)`.

**Accent ramp** — 100 `#f5f4ff`, 200 `#e7e5fe`, 300 `#d2cefd`, 400 `#b5abfc`, 500 `#968ae0`, 600 `#796cbf`, 700 `#5d5294`, 800 `#423a6a`, 900 `#2b2741`.

**Neutral ramp (used here)** — 800 `#292b31`, 900 `#292b31`; hairlines `#3f424d`, `#595d6c`.

**Extra surfaces used in this design** — `#1b1d2c` (header gradient end), `#1d1f2c` (answer block, heatmap floor), `#221f36` (brief gradient start), `#3a3455` (low heat step), `#5c2b33`/`#f6e3e6` (suspension chip), `#2b3a33`/`#dbeee4` (commendation chip), `#243329`/`#d6ecdd` (Sheets chip).

**Spacing** (density 0.70×) — `--space-1 2.8px`, `-2 5.6px`, `-3 8.4px`, `-4 11.2px`, `-6 16.8px`, `-8 22.4px`. Layout also uses 14px, 19px and 28px gaps/padding.

**Radii** — `--radius-sm 4px`, `--radius-md 8px`, `--radius-lg 14px`.

**Shadows** — `--shadow-sm 0 0 0 1px #3f424d`; `--shadow-md 0 0 0 1px #595d6c, 0 6px 18px rgba(0,0,0,0.55)`; `--shadow-lg 0 0 0 1px #9397ab, 0 16px 40px rgba(0,0,0,0.65)`. On this dark ground, elevation is an edge plus ambient darkness — don't stack shadows.

**Type** — Inter for both headings and body (`--font-heading` / `--font-body`), headings at weight 500 and never heavier. Sizes in use: 26px h1; 18px section h2; 16px card h2; 15px panel label; 14.5/14px card titles; 13.5/13/12.5px body; 12/11.5/11/10.5px meta; 10px uppercase kickers with `letter-spacing 0.1–0.12em`. Muted text is the text color through `color-mix` at 78 / 70 / 62 / 55 / 48 / 45 / 42 / 40 / 38 / 35%.

**Design-system rules worth honoring** — primary buttons are an accent *outline*, never a fill; rules fade to transparent over 48px at each end; keep chroma low outside the accent; no pure black or white; `.lighten` wraps any photograph.

## Assets

None. No images, no icon set is used in the mock — the only glyphs are the brand letter, the `+`/`–` panel marks and text. The design system specifies **Phosphor icons** (phosphoricons.com) if you add any; the mock deliberately ships without them rather than drawing approximations.

## Files

- `reference/Teacher View.dc.html` — the full design reference. Open directly in a browser. Everything above is in this file; the logic class at the bottom holds the sample data (12 students, 4 classes) and every derived value.
- `reference/support.js` — the runtime the reference file needs to render. Do not port.
- `reference/_ds/nocturne-28b6daff-ee54-471a-a272-76516a9b54a4/styles.css` — design-system tokens and component classes. Port these tokens into the Tailwind theme.
- `reference/_ds/nocturne-28b6daff-ee54-471a-a272-76516a9b54a4/_ds_bundle.js` — the design-system component bundle the reference loads.
- In the repo: `docs/spec.md` (endpoints, phases, seed-data approach), `passport/models.py` (`Student`, `Classroom`, `StudentRecord`, `Passport`), `README.md` (the three views).

## Note on the sample data

All twelve students are synthetic, written as correlated story arcs the way `docs/spec.md` describes seed data: a Monday attendance dip that resolves to a guardian's night shift; pre-lunch behavior flags that resolve to a missed breakfast window; a reading IEP where comprehension outruns decoding; and three deliberately thin passports. Use them as fixtures for the empty states and the "signal you can actually find" demo, not as real content.
