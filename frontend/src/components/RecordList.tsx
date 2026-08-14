import { SOURCE_LABELS, type StudentRecord } from '../api/types';
import { formatDate } from '../lib/school';

export function SourceBadge({ source }: { source: StudentRecord['source'] }) {
  return (
    <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-0.5 text-xs font-medium text-slate-600">
      {SOURCE_LABELS[source]}
    </span>
  );
}

export function RecordList({
  records,
  empty,
}: {
  records: StudentRecord[];
  empty: string;
}) {
  if (records.length === 0) {
    return <p className="text-sm text-slate-500">{empty}</p>;
  }
  return (
    <ol className="space-y-4">
      {records.map((record) => (
        <li
          key={record.id}
          className="rounded-lg border border-slate-200 bg-white p-4"
        >
          <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <h3 className="font-medium text-slate-900">{record.title}</h3>
            <SourceBadge source={record.source} />
            <time
              dateTime={record.date}
              className="ml-auto text-sm text-slate-500 tabular-nums"
            >
              {formatDate(record.date)}
            </time>
          </div>
          {record.body && (
            <p className="mt-2 leading-relaxed text-slate-600">{record.body}</p>
          )}
          {record.author && (
            <p className="mt-2 text-sm text-slate-500">— {record.author}</p>
          )}
        </li>
      ))}
    </ol>
  );
}
