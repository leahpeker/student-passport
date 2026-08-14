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
  { stroke: '#968ae0', dash: '0' },
  { stroke: '#d2cefd', dash: '7 4' },
  { stroke: '#5d5294', dash: '2 3' },
  { stroke: '#9690c9', dash: '10 3 2 3' },
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
        <p className="text-[13px] text-muted">No assessment scores on record.</p>
      ) : (
        <ChartFigure
          caption="Assessment scores by month, out of 100."
          summary={
            <>
              Across the year:{' '}
              {subjects.map((subject, i) => (
                <span key={subject}>
                  {i > 0 && '; '}
                  <span className="font-medium text-text">{subject}</span> is{' '}
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
              <CartesianGrid stroke="#3f424d" vertical={false} />
              <XAxis
                dataKey="month"
                stroke="#75798c"
                tickLine={false}
                fontSize={12}
              />
              <YAxis
                domain={[0, 100]}
                stroke="#75798c"
                tickLine={false}
                fontSize={12}
              />
              <Tooltip
                contentStyle={{
                  background: '#232532',
                  border: '1px solid #3f424d',
                  borderRadius: 8,
                  fontSize: 13,
                }}
                labelStyle={{ color: '#e9e9ed' }}
                itemStyle={{ color: '#e9e9ed' }}
              />
              <Legend wrapperStyle={{ fontSize: 12, color: '#e9e9ed' }} />
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
