# Cognitive Task Analysis: Priya Raghunathan (Grade 11) — School Year 2025–2026

## Snapshot

Across 16 sessions and nine months, Priya's AI tutor use splits almost perfectly into two different students. In her self-directed sessions — Gödel's incompleteness theorem, P vs NP, a garbage collector she wants to build, a homotopy type theory paper she wants to eventually read — she drives the whole conversation: she states her own model, tests it against a worry she generated herself, and corrects it live when it's wrong. In her assigned-homework sessions, she hands the whole thing over, often within one turn, and rarely looks at what comes back. The single most important thing to know: this is not a student who can't engage or won't think hard. It's a student whose engagement is almost entirely gated on whether the task is hers.

**Evidence base:** 55 student turns across 16 sessions spanning September 2025 to May 2026, across five subject areas. The split between self-directed and assigned sessions is itself the clearest and most stable finding in the corpus.

## Cognitive profile

| Task type | Presence | Typical depth | Peak | Notes |
|---|---|---|---|---|
| Fluency | Not observed | — | — | Neither her advanced self-directed material nor her offloaded homework produced a quick-recall turn |
| Procedural | Frequent | Surface | Rebuilding a measurability proof correctly from a corrected principle | Real when the problem is hers; clean-offloaded when it's a worksheet she's already mastered |
| Conceptual | Frequent | Substantive | Naming that a garbage collector's memory region *is* the timestamp, unprompted | Her clearest and most consistent strength — the default mode of her self-directed sessions, not a one-off peak |
| Critical Thinking | Frequent | Developing | Rejecting "most people believe P≠NP" as a headcount, not an argument | Skeptical of consensus claims specifically, not just of the tutor |
| Creative | Not observed | — | — | Every writing-shaped request (reading response, discussion post, essay) was handed off whole |
| Metacognitive | Frequent | Developing | Naming her own motivation for unassigned extra work, unprompted, in May | Sharp and precise the moment she's asked; rarely volunteered outside self-directed sessions |
| Transfer | Frequent | Substantive | Synthesizing two of her own earlier sessions into a single self-assessment | Unusually frequent for this type, which is normally the rarest in a transcript |
| Exploratory | Frequent | Developing | Deciding to go find Gödel's original paper rather than stop at the explanation | Nearly every self-directed session opens this way, and it almost always converts into Conceptual work within a turn or two |

For a single session, typical and peak depth usually match; across this many sessions the two diverge for Procedural specifically — the clearest and most useful line in this table, since it maps directly onto whether the task was hers.

## What the evidence shows

### Conceptual — building and repairing mental models on her own material

This is not a peak, it's a pattern. In a session about series rearrangement, she opens by asking why a theorem "doesn't break physics," gets an answer, and then corrects her own framing: "wait so it's not actually that physics is automatically safe from the rearrangement problem, it's that either the series happens to converge absolutely, or it doesn't even converge in the first place... that's a different claim than 'physics doesn't have this problem'" (T19, sess_44eebb31). In a measure theory problem set from her uncle, she pastes her own attempted proof, is told there's a gap, and immediately states the fix precisely: "wait, so I can't just assume it's measurable because it seems sparse, I actually have to build it as a countable intersection of sets I already know are measurable" (T49, sess_b804f652) — then rebuilds the full argument correctly and unprompted (T51). The clearest single instance is smaller: asking how a garbage collector tracks object age without expensive per-object timestamps, she's told the memory region itself encodes it, and in one sentence she reframes her whole assumption: "oh, so the region IS the timestamp, you don't need to store one anywhere because location already encodes age. that's actually elegant, I was assuming it had to be metadata attached to the object itself" (T80, sess_19bc7740).

### Critical Thinking — skeptical of consensus, not just of the tutor

Asked about P vs NP, she's told the field generally believes P≠NP. She doesn't accept that as an answer: "ok but 'most people believe' isn't an argument, it's a headcount. what's the actual reasoning behind leaning P≠NP if nobody's proved it" (T36, sess_5f60a2e9) — and once given the actual structural reasons, synthesizes them herself: "so people have basically proven a giant list of ways you CANNOT prove it, without proving the thing itself. that's kind of funny when you say it like that" (T38). The same instinct shows up on a math problem: given a technically valid alternate proof of the quadratic formula, she rejects it against her own standard — "that's not really shorter, it's just a different flavor of the same grinding. I want to know if there's one that doesn't feel like a trick" (T71, sess_f3a58d02) — and only accepts the next one once she can say why it's structurally different, not just correct.

### Transfer — unusually frequent for this type

Transfer is normally the rarest type in a student transcript. Priya produces it four times, unprompted, across the year: connecting Gödel's construction to Cantor's diagonal argument in her very first self-directed session ("wait, that's the same trick Cantor used isn't it," T3, sess_7a2f19c4); generalizing the open status of P vs NP to NP vs coNP (T40, sess_5f60a2e9); connecting type inference undecidability to a related but distinct problem in dependent types (T61, sess_de77b93f); and, most strikingly, connecting two of her *own* earlier sessions to plan a new goal — "I already sort of have the type theory part from the garbage collector and type inference stuff I went through earlier this year. so really what's missing is the category theory and the homotopy piece" (T86, sess_d0e9b256). That last instance is Transfer applied to her own learning history, which is a rarer and more mature move than Transfer applied to course content.

### Metacognitive — precise when asked, otherwise quiet

Her clearest metacognitive moment closes the whole corpus. Asked what she got out of shipping a compiler project that went well beyond the assignment, she doesn't perform modesty or ambition — she states the mechanism plainly: "nothing I can put on a transcript. I just wanted to see if I could actually get it to run, the assignment was basically an excuse" (T93, sess_837f1a6c). Earlier in the year, after resolving a conceptual confusion, she names exactly what had been bothering her about how her textbook phrased it (T21, sess_44eebb31) — precise self-diagnosis, not just relief at getting the right answer.

### Exploratory — the default opening move, rarely the ending point

Nearly every self-directed session in this transcript opens with an orienting question outside the syllabus — Gödel, P vs NP, what comes after loops, type inference, a compiler roadmap. What's notable is how rarely it stays purely Exploratory: within a turn or two it typically converts into Conceptual or Transfer work. The purest Exploratory instance is a closing move rather than an opening one: after being told incompleteness is mostly a philosophical asterisk for working mathematicians, she decides on her own next step — "ok that's kind of unsettling actually, in a good way. I'm going to go find the actual paper instead of just explanations of it" (T9, sess_7a2f19c4).

## Where thinking was offloaded

Six instances, and the pattern is sharp. Three of six are writing assignments handed off whole: a reading response for a chapter she hadn't read ("I didn't read it, just write something plausible," T24, sess_902fca7d), a full History essay the night it was due ("no I genuinely do not care, midnight deadline, just write it," T44, sess_ee3d17ab), and a discussion post described by late April as routine — "same as always, just write me a discussion post" (T81, sess_ac402ef1). Two more are math worksheets on content she'd already scored 90%+ on elsewhere in her record: a logarithms set and a rational-functions set, both submitted as "answers only for these 8, no work needed," both declining the tutor's offer to walk through anything (T10, T54). The sixth is the only instance with any inspection at all — a physics problem set solved for her outright, followed by one real but narrow question about a sign convention (T66, sess_66021ce8).

None of this touches her self-directed sessions. Not one offload instance appears outside an assigned task, and every writing-shaped assignment in the transcript without exception was offloaded — creative work is the one type that never once shows up as her own.

## What's missing

Fluency and Creative are the two types absent from this transcript, for different reasons. Fluency is absent because neither pole of her AI tutor use produces it: her self-directed sessions are all frontier material she's building from scratch, not settled facts she's confirming, and her homework sessions are handed off before any recall would happen. That's a "task never required it" absence, not a gap in her.

Creative is different, and more worth a teacher's attention. Every writing-shaped request in this transcript — three of them, across two subjects — was offloaded completely, with no original material of hers in the result. This isn't a capability question; nothing here suggests she can't write. It's that writing assignments in this transcript never once got the "generate first" treatment her math and CS curiosity gets by default.

## For the teacher

**Require an attempt before the full draft, specifically on writing assignments.** Every offload but one this year was a piece of writing handed over whole. Ask for one sentence of her own reaction or thesis before she's allowed to bring it to a tutor for a full draft — the same move the tutor already tries in these transcripts and she currently overrides.

**Stop assigning her worksheets on content she's already tested out of.** Her two clean procedural offloads were both on material she'd already scored 90%+ on. Swap those for a problem that costs her something — an extension, or "find where this method breaks" — rather than routine practice with nothing left in it to learn.

**Give Transfer a legitimate outlet inside class, roughly weekly.** She produces it four times unprompted, including once by connecting two of her own separate self-directed sessions into a plan. That's a proven, habitual capability currently running entirely outside school hours.

**Ask her directly, once a grading period, what she got out of something versus what it earned her.** Turn 93 — "nothing I can put on a transcript... the assignment was basically an excuse" — is the most honest and precise line in the whole corpus, and nothing in her currently graded work asks the question that produced it.

## Caveats

This reflects one AI tutor across one school year — it doesn't capture in-class work, the problem sets her uncle sends her outside any recorded system, or conversations with teachers. The sessions here are self-selected: she brought what she was stuck on or curious about, which skews the sample away from whatever routine work she handles easily without asking for help at all. Depth ratings reflect what she wrote in the moment, not independently verified retention. And the sharp split between self-directed and assigned-homework sessions may partly reflect which kind of task she chooses to bring to an AI tutor in the first place, not only how she engages once she's there.
