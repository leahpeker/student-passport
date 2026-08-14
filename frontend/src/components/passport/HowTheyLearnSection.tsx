import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from 'recharts';
import type { StudentRecord } from '../../api/types';
import { engagementByPeriod } from '../../lib/school';
import { ChartFigure } from '../ChartFigure';
import { Section } from '../Section';

export function HowTheyLearnSection({
  records,
  narrative,
}: {
  records: StudentRecord[];
  narrative: string;
}) {
  const points = engagementByPeriod(records);
  const ranked = [...points].sort((a, b) => b.rating - a.rating);
  const best = ranked[0];
  const worst = ranked[ranked.length - 1];
  const samples = points.reduce((total, p) => total + p.samples, 0);

  return (
    <Section id="how-they-learn" title="How they learn" lead={narrative}>
      {points.length === 0 ? (
        <p className="text-[13px] text-muted">No engagement samples on record.</p>
      ) : (
        <ChartFigure
          caption="Average engagement rating by period, out of 5."
          summary={
            <>
              Highest in{' '}
              <span className="font-medium text-text">{best.period}</span> at{' '}
              {best.rating.toFixed(1)} and lowest in{' '}
              <span className="font-medium text-text">{worst.period}</span> at{' '}
              {worst.rating.toFixed(1)}, from {samples} samples across the year.
              Each bar is printed with its own value.
            </>
          }
          table={{
            headers: ['Period', 'Average rating', 'Samples'],
            rows: points.map((p) => [p.period, p.rating.toFixed(1), p.samples]),
          }}
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={points}
              margin={{ top: 20, right: 16, bottom: 0, left: -16 }}
              accessibilityLayer={false}
            >
              <CartesianGrid stroke="#3f424d" vertical={false} />
              <XAxis
                dataKey="period"
                stroke="#75798c"
                tickLine={false}
                fontSize={12}
              />
              <YAxis domain={[0, 5]} stroke="#75798c" tickLine={false} fontSize={12} />
              <Bar dataKey="rating" fill="#968ae0" radius={[4, 4, 0, 0]}>
                <LabelList
                  dataKey="rating"
                  position="top"
                  fontSize={12}
                  fill="#e9e9ed"
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartFigure>
      )}
    </Section>
  );
}
