import type { Student } from '../../api/types';
import type { Pulse } from '../../lib/pulse';
import { metricText, toneCard, toneDot, toneLabel, toneText, trendArrow } from './tone';

/**
 * The pulse, as the hero of the profile row. A high-level, semi-permanent read
 * — status, why, what changed, the signals and the surrounding context — that
 * expands into the assistant for the full picture and a suggested next step.
 */
export function PulseHero({
  student,
  pulse,
  onAsk,
}: {
  student: Student;
  pulse: Pulse;
  onAsk: (prompt?: string) => void;
}) {
  return (
    <section
      aria-label={`Pulse for ${student.name}`}
      className={`flex flex-col rounded-lg border p-4 ${toneCard[pulse.tone]}`}
    >
      <div className="mb-3 flex items-center justify-between">
        <span className="text-[10.5px] font-medium tracking-[0.1em] text-muted uppercase">
          Pulse · this week
        </span>
        <button
          type="button"
          onClick={() => onAsk()}
          className={`text-[11px] font-semibold ${toneText[pulse.tone]} hover:underline`}
        >
          Expand ⤢
        </button>
      </div>

      <div className="grid flex-1 gap-5 sm:grid-cols-[1.1fr_1fr]">
        {/* left: status + why + since */}
        <div>
          <div className="flex items-center gap-3">
            <span className="flex flex-col gap-1" aria-hidden="true">
              <span className={`h-3.5 w-3.5 rounded-full ${pulse.tone === 'red' ? toneDot.red : 'bg-neutral-700'}`} />
              <span className={`h-3.5 w-3.5 rounded-full ${pulse.tone === 'amber' ? toneDot.amber : 'bg-neutral-700'}`} />
              <span className={`h-3.5 w-3.5 rounded-full ${pulse.tone === 'green' ? toneDot.green : 'bg-neutral-700'}`} />
            </span>
            <div>
              <p className={`text-[17px] font-semibold ${toneText[pulse.tone]}`}>
                {pulse.headline}
              </p>
              <p className="text-[11px] text-muted">
                {pulse.trendNote} · {toneLabel[pulse.tone]}
              </p>
            </div>
          </div>

          <p className="mt-3 text-[12.5px] leading-relaxed text-text/80">{pulse.why}</p>

          <p className="mt-3 text-[9px] font-semibold tracking-[0.08em] text-muted uppercase">
            Since your last visit · {pulse.since.asOf}
          </p>
          <ul className="mt-1 space-y-0.5">
            {pulse.since.changes.slice(0, 2).map((c, i) => (
              <li key={i} className="flex gap-2 text-[11.5px] text-text/80">
                <span aria-hidden="true" className={`font-semibold ${toneText[pulse.tone]}`}>
                  {c.direction === 'up' ? '↑' : c.direction === 'down' ? '↓' : '+'}
                </span>
                {c.text}
              </li>
            ))}
          </ul>
        </div>

        {/* right: signals + context */}
        <div>
          <p className="text-[9px] font-semibold tracking-[0.08em] text-muted uppercase">
            Signals driving this
          </p>
          <ul className="mt-1">
            {pulse.signals.map((s) => (
              <li key={s.label} className="border-b border-divider last:border-0">
                <button
                  type="button"
                  onClick={() => onAsk(`Tell me about ${student.first_name}'s ${s.label.toLowerCase()}`)}
                  className="flex w-full items-center gap-2 py-1.5 text-left hover:opacity-80"
                >
                  <span className="flex-1 text-[11.5px] font-medium text-text/85">
                    {s.label}
                  </span>
                  <span
                    aria-hidden="true"
                    className={`text-[12px] font-semibold ${s.concerning ? toneText[pulse.tone] : 'text-muted'}`}
                  >
                    {trendArrow(s.trend)}
                  </span>
                </button>
              </li>
            ))}
          </ul>

          <ul className="mt-3 flex flex-wrap gap-1.5">
            {pulse.context.map((c) => (
              <li
                key={c.label}
                className="rounded-md bg-bg/40 px-2 py-1 text-[10px] text-muted"
              >
                {c.label} <span className={metricText[c.tone]}>{c.value}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => onAsk(`What should I do to support ${student.first_name}?`)}
          className="btn btn-primary"
        >
          ✦ Open assistant
        </button>
        <span className="text-[11px] text-muted">
          Get the full picture &amp; a suggested next step
        </span>
      </div>
    </section>
  );
}
