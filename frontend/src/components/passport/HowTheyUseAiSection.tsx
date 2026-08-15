import { useMemo, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { StudentRecord } from '../../api/types';
import {
  cognitiveSubjects,
  cognitiveTypePoints,
  cognitiveTypeShares,
  cognitiveTypeSharesBySubject,
  formatDate,
  latestCognitiveAnalysis,
} from '../../lib/school';
import { ChartFigure } from '../ChartFigure';
import { Section } from '../Section';

const DEPTH_LABELS = ['Not observed', 'Surface', 'Developing', 'Substantive'];

const PATTERN_LABELS: Record<string, string> = {
  clean_offload: 'Handed off, nothing done with it after',
  offload_with_inspection: 'Handed off, then checked or questioned',
  scaffolded_offload: 'Handed off, tutor scaffolded instead of complying',
  escalating_offload: 'Asked more than once, with rising pressure',
};

/**
 * Fixed hue per cognitive type, in the skill's canonical order — color must
 * follow the type's identity, never its share, so a student whose ranking
 * differs from another's still shows the same type in the same color.
 * Validated (CVD ΔE, contrast, lightness/chroma) against this app's chart
 * surface (#232532) via the dataviz skill's validator.
 */
const TYPE_COLORS: Record<string, string> = {
  fluency: '#3987e5',
  procedural: '#d95926',
  conceptual: '#199e70',
  critical_thinking: '#c98500',
  creative: '#d55181',
  metacognitive: '#008300',
  transfer: '#9085e9',
  exploratory: '#e66767',
};

const CHART_SURFACE = '#232532';
const ALL_SUBJECTS = 'All';

function FilterPill({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={`tag cursor-pointer ${active ? 'tag-accent' : 'tag-outline'}`}
    >
      {label}
    </button>
  );
}

export function HowTheyUseAiSection({
  records,
  narrative,
}: {
  records: StudentRecord[];
  narrative: string;
}) {
  const analysis = latestCognitiveAnalysis(records);
  const [subject, setSubject] = useState<string>(ALL_SUBJECTS);

  const subjects = useMemo(() => (analysis ? cognitiveSubjects(analysis) : []), [analysis]);
  const shares = useMemo(() => {
    if (!analysis) return [];
    return subject === ALL_SUBJECTS
      ? cognitiveTypeShares(analysis)
      : cognitiveTypeSharesBySubject(analysis, subject);
  }, [analysis, subject]);
  const totalInstances = shares.reduce((sum, s) => sum + s.count, 0);

  return (
    <Section id="how-they-use-ai" title="How they use AI" lead={narrative}>
      {!analysis ? (
        <p className="text-[13px] text-muted">No AI-use analysis on record.</p>
      ) : (
        <>
          <ChartFigure
            caption="Depth of thinking by cognitive type, from AI-tutor sessions."
            summary={
              <>
                Typical is where {analysis.evidence_base.session_count} sessions
                usually land; peak is the best single instance of each type.
                Based on {analysis.evidence_base.sufficiency} evidence.
              </>
            }
            table={{
              headers: ['Cognitive type', 'Typical depth', 'Peak depth'],
              rows: cognitiveTypePoints(analysis).map((p) => [
                p.label,
                DEPTH_LABELS[p.typical],
                DEPTH_LABELS[p.peak],
              ]),
            }}
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={cognitiveTypePoints(analysis)}
                margin={{ top: 8, right: 16, bottom: 0, left: -16 }}
                barGap={2}
                accessibilityLayer={false}
              >
                <CartesianGrid stroke="#3f424d" vertical={false} />
                <XAxis
                  dataKey="label"
                  stroke="#75798c"
                  tickLine={false}
                  fontSize={11}
                  interval={0}
                  angle={-25}
                  textAnchor="end"
                  height={56}
                />
                <YAxis
                  domain={[0, 3]}
                  ticks={[0, 1, 2, 3]}
                  tickFormatter={(v: number) => String(v)}
                  stroke="#75798c"
                  tickLine={false}
                  fontSize={12}
                />
                <Legend wrapperStyle={{ fontSize: 12, color: '#e9e9ed' }} />
                <Bar dataKey="typical" name="Typical depth" fill="#968ae0" radius={[3, 3, 0, 0]} />
                <Bar dataKey="peak" name="Peak depth" fill="#5d5294" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartFigure>

          <h3 className="mt-8 mb-3 text-[14px] font-medium text-text">
            Where the sessions went
          </h3>

          <div className="mb-4 flex flex-wrap items-start gap-x-8 gap-y-3">
            <div>
              <div className="mb-1.5 text-[10.5px] font-medium tracking-[0.08em] text-muted uppercase">
                Subject
              </div>
              <div className="flex flex-wrap gap-1.5">
                <FilterPill
                  label={ALL_SUBJECTS}
                  active={subject === ALL_SUBJECTS}
                  onClick={() => setSubject(ALL_SUBJECTS)}
                />
                {subjects.map((s) => (
                  <FilterPill key={s} label={s} active={subject === s} onClick={() => setSubject(s)} />
                ))}
              </div>
            </div>
            <div>
              <div className="mb-1.5 text-[10.5px] font-medium tracking-[0.08em] text-muted uppercase">
                Tutor
              </div>
              <div className="flex flex-wrap gap-1.5">
                <FilterPill label={ALL_SUBJECTS} active onClick={() => {}} />
              </div>
              <p className="mt-1.5 text-[11px] text-muted">
                One AI tutor is used throughout this app, so there is nothing to filter by yet.
              </p>
            </div>
          </div>

          {totalInstances === 0 ? (
            <p className="text-[13px] text-muted">
              No {subject === ALL_SUBJECTS ? '' : `${subject} `}sessions showed any cognitive-type
              activity to chart.
            </p>
          ) : (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <div aria-hidden="true" className="h-56 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Tooltip
                      formatter={(value, _name, item) => {
                        const count = Number(value);
                        const payload = item.payload as { share: number; label: string };
                        return [
                          `${count} instance${count === 1 ? '' : 's'} (${payload.share.toFixed(1)}%)`,
                          payload.label,
                        ];
                      }}
                      contentStyle={{
                        background: '#232532',
                        border: '1px solid #3f424d',
                        borderRadius: 8,
                        fontSize: 13,
                      }}
                      labelStyle={{ color: '#e9e9ed' }}
                      itemStyle={{ color: '#e9e9ed' }}
                    />
                    <Pie
                      data={shares}
                      dataKey="count"
                      nameKey="label"
                      outerRadius="88%"
                      stroke={CHART_SURFACE}
                      strokeWidth={2}
                      isAnimationActive
                      animationBegin={0}
                      animationDuration={450}
                      animationEasing="ease-out"
                    >
                      {shares.map((s) => (
                        <Cell key={s.id} fill={TYPE_COLORS[s.id]} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div className="overflow-x-auto">
                <table className="table">
                  <caption className="sr-only">
                    Share of recorded instances by cognitive type
                    {subject === ALL_SUBJECTS ? '' : `, ${subject} only`}
                  </caption>
                  <thead>
                    <tr>
                      <th scope="col">Cognitive type</th>
                      <th scope="col">Instances</th>
                      <th scope="col">Share</th>
                    </tr>
                  </thead>
                  <tbody>
                    {shares.map((s) => (
                      <tr key={s.id}>
                        <th scope="row" className="text-left font-normal text-text/85">
                          <span className="inline-flex items-center gap-2">
                            <span
                              aria-hidden="true"
                              className="inline-block h-2.5 w-2.5 shrink-0 rounded-sm"
                              style={{ backgroundColor: TYPE_COLORS[s.id] }}
                            />
                            {s.label}
                          </span>
                        </th>
                        <td className="tabular-nums text-muted">{s.count}</td>
                        <td>
                          <div className="flex items-center gap-2">
                            <span className="w-12 shrink-0 tabular-nums text-muted">
                              {s.share.toFixed(1)}%
                            </span>
                            <span className="h-1.5 w-full min-w-[48px] overflow-hidden rounded-full bg-[var(--surface-well)]">
                              <span
                                className="block h-full rounded-full"
                                style={{
                                  width: `${s.share}%`,
                                  backgroundColor: TYPE_COLORS[s.id],
                                }}
                              />
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {analysis.offloading.instance_count > 0 && (
            <details className="mt-6 rounded-lg bg-[var(--surface-well)] px-4 py-3 text-[13px] text-text/85">
              <summary className="cursor-pointer">
                <span className="font-medium text-text">Offloading:</span>{' '}
                {analysis.offloading.instance_count} instance
                {analysis.offloading.instance_count === 1 ? '' : 's'} where the
                thinking went to the AI instead of the student.{' '}
                {analysis.offloading.summary}
              </summary>
              <ol className="mt-4 space-y-4 border-t border-white/10 pt-4">
                {analysis.offloading.instances.map((inst, i) => (
                  <li key={`${inst.session_id}-${inst.turn_id}-${i}`}>
                    <div className="flex flex-wrap items-baseline gap-x-2 text-[11px] text-muted">
                      <time dateTime={inst.date}>{formatDate(inst.date)}</time>
                      <span aria-hidden="true">·</span>
                      <span>{inst.subject}</span>
                      <span className="tag tag-neutral">
                        {(analysis.cognitive_types.find((t) => t.id === inst.type_offloaded)
                          ?.label) ?? inst.type_offloaded}
                      </span>
                      <span className="tag tag-accent2">
                        {PATTERN_LABELS[inst.pattern] ?? inst.pattern}
                      </span>
                    </div>
                    <p className="mt-1.5 text-text/90 italic">"{inst.student_turn.text}"</p>
                    {inst.note && <p className="mt-1 text-muted">{inst.note}</p>}
                  </li>
                ))}
              </ol>
            </details>
          )}
        </>
      )}
    </Section>
  );
}
