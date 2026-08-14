import { SOURCE_LABELS, type StudentRecord } from '../api/types';
import { formatDate } from '../lib/school';

const SOURCE_TAG_CLASS: Record<StudentRecord['source'], string> = {
  sis: 'tag-neutral',
  assessment: 'tag-neutral',
  attendance: 'tag-neutral',
  behavior: 'tag-neutral',
  engagement: 'tag-neutral',
  document: 'tag-accent2',
  observation: 'tag-accent',
  parent_input: 'tag-accent',
  student_input: 'tag-accent',
  ai_tutor: 'tag-accent',
  question: 'tag-accent',
};

export function SourceBadge({ source }: { source: StudentRecord['source'] }) {
  return (
    <span className={`tag ${SOURCE_TAG_CLASS[source]}`}>
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
    return <p className="text-[13px] text-muted">{empty}</p>;
  }
  return (
    <ol className="space-y-3">
      {records.map((record) => (
        <li key={record.id} className="card">
          <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <h3 className="text-[13.5px] font-medium text-text">
              {record.title}
            </h3>
            <SourceBadge source={record.source} />
            <time
              dateTime={record.date}
              className="ml-auto text-[11px] text-muted tabular-nums"
            >
              {formatDate(record.date)}
            </time>
          </div>
          {record.body && (
            <p className="text-[12.5px] leading-relaxed text-text/80">
              {record.body}
            </p>
          )}
          {record.author && (
            <p className="text-[11px] text-muted">— {record.author}</p>
          )}
        </li>
      ))}
    </ol>
  );
}
