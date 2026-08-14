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
import { absencesByWeekday, behaviorByPeriod, behaviorOverTime } from '../../lib/school';
import { ChartFigure } from '../ChartFigure';
import { RecordList } from '../RecordList';
import { Section } from '../Section';

export function BehaviorSection({
  records,
  narrative,
}: {
  records: StudentRecord[];
  narrative: string;
}) {
  const points = behaviorOverTime(records);
  const total = points.reduce((sum, p) => sum + p.incidents, 0);

  const byPeriod = Object.entries(behaviorByPeriod(records))
    .map(([period, count]) => ({ period: Number(period), count }))
    .sort((a, b) => b.count - a.count);
  const topPeriod = byPeriod[0];

  const byWeekday = Object.entries(absencesByWeekday(records)).sort(
    (a, b) => b[1] - a[1],
  );
  const topWeekday = byWeekday[0];
  const absences = byWeekday.reduce((sum, [, count]) => sum + count, 0);

  const entries = records
    .filter((r) => r.source === 'behavior' || r.source === 'observation')
    .slice(0, 5);

  return (
    <Section id="behavior" title="Behaviour over time" lead={narrative}>
      <ChartFigure
        caption="Behaviour entries logged each month."
        summary={
          <>
            {total} entries across the year
            {topPeriod && topPeriod.count > 0 && (
              <>
                , with the largest cluster in{' '}
                <span className="font-medium text-text">
                  period {topPeriod.period}
                </span>{' '}
                ({topPeriod.count} of them)
              </>
            )}
            . Each bar is printed with its own count.
          </>
        }
        table={{
          headers: ['Month', 'Entries'],
          rows: points.map((p) => [p.month, p.incidents]),
        }}
      >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={points}
            margin={{ top: 20, right: 16, bottom: 0, left: -16 }}
            accessibilityLayer={false}
          >
            <CartesianGrid stroke="#3f424d" vertical={false} />
            <XAxis dataKey="month" stroke="#75798c" tickLine={false} fontSize={12} />
            <YAxis
              allowDecimals={false}
              stroke="#75798c"
              tickLine={false}
              fontSize={12}
            />
            <Bar dataKey="incidents" fill="#5d5294" radius={[4, 4, 0, 0]}>
              <LabelList
                dataKey="incidents"
                position="top"
                fontSize={12}
                fill="#e9e9ed"
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </ChartFigure>

      {absences > 0 && topWeekday && (
        <p className="mt-6 rounded-lg bg-[var(--surface-well)] px-4 py-3 text-[13px] text-text/85">
          <span className="font-medium text-text">Attendance:</span>{' '}
          {absences} full-day absences on record. {topWeekday[0]} accounts for{' '}
          {topWeekday[1]} of them, more than any other weekday.
        </p>
      )}

      <h3 className="mt-8 mb-3 text-[14px] font-medium text-text">
        Most recent entries and observations
      </h3>
      <RecordList records={entries} empty="Nothing on record." />
    </Section>
  );
}
