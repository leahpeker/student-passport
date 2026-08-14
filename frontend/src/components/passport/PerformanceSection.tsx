import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { StudentRecord } from '../../api/types';
import { performanceOverTime } from '../../lib/school';
import { ChartFigure } from '../ChartFigure';
import { Section } from '../Section';

/** Each series gets its own colour *and* its own line style. */
const SERIES = [
  { stroke: '#4338ca', dash: '0' },
  { stroke: '#0f766e', dash: '7 4' },
  { stroke: '#b45309', dash: '2 3' },
  { stroke: '#9d174d', dash: '10 3 2 3' },
];

function describe(change: number): string {
  if (change > 4) return `up ${change} points`;
  if (change < -4) return `down ${Math.abs(change)} points`;
  return 'level';
}

export function PerformanceSection({
  records,
  narrative,
}: {
  records: StudentRecord[];
  narrative: string;
}) {
  const { subjects, points, change } = performanceOverTime(records);

  return (
    <Section id="performance" title="Performance over time" lead={narrative}>
      {points.length === 0 ? (
        <p className="text-sm text-slate-500">No assessment scores on record.</p>
      ) : (
        <ChartFigure
          caption="Assessment scores by month, out of 100."
          summary={
            <>
              Across the year:{' '}
              {subjects.map((subject, i) => (
                <span key={subject}>
                  {i > 0 && '; '}
                  <span className="font-medium text-slate-900">{subject}</span> is{' '}
                  {describe(change[subject])}
                </span>
              ))}
              .
            </>
          }
          table={{
            headers: ['Month', ...subjects],
            rows: points.map((point) => [
              String(point.month),
              ...subjects.map((subject) =>
                typeof point[subject] === 'number' ? point[subject] : '—',
              ),
            ]),
          }}
        >
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={points}
              margin={{ top: 8, right: 16, bottom: 0, left: -16 }}
              accessibilityLayer={false}
            >
              <CartesianGrid stroke="#e2e8f0" vertical={false} />
              <XAxis
                dataKey="month"
                stroke="#94a3b8"
                tickLine={false}
                fontSize={12}
              />
              <YAxis
                domain={[0, 100]}
                stroke="#94a3b8"
                tickLine={false}
                fontSize={12}
              />
              <Tooltip />
              <Legend />
              {subjects.map((subject, i) => {
                const style = SERIES[i % SERIES.length];
                return (
                  <Line
                    key={subject}
                    type="monotone"
                    dataKey={subject}
                    stroke={style.stroke}
                    strokeWidth={2.5}
                    strokeDasharray={style.dash}
                    dot={{ r: 3 }}
                    connectNulls
                  />
                );
              })}
            </LineChart>
          </ResponsiveContainer>
        </ChartFigure>
      )}
    </Section>
  );
}
