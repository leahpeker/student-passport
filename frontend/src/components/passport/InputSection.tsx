import { useState } from 'react';
import { submitInput } from '../../api/client';
import type { InputSubmission, StudentRecord } from '../../api/types';
import { RecordList } from '../RecordList';
import { Section } from '../Section';

/**
 * Guardian input and student input. Same shape, different source, so one
 * component covers both sections.
 */
export function InputSection({
  id,
  title,
  lead,
  source,
  studentId,
  records,
  canWrite,
  formLabel,
  onAdded,
}: {
  id: string;
  title: string;
  lead: string;
  source: InputSubmission['source'];
  studentId: number;
  records: StudentRecord[];
  canWrite: boolean;
  formLabel: string;
  onAdded: (record: StudentRecord) => void;
}) {
  const [heading, setHeading] = useState('');
  const [body, setBody] = useState('');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (body.trim() === '') return;
    setPending(true);
    setError(null);
    try {
      const record = await submitInput(studentId, {
        source,
        title: heading.trim() || formLabel,
        body: body.trim(),
      });
      onAdded(record);
      setHeading('');
      setBody('');
      setSaved(true);
    } catch {
      setError('That could not be saved. Try again.');
    } finally {
      setPending(false);
    }
  }

  return (
    <Section id={id} title={title} lead={lead}>
      <RecordList records={records} empty="Nothing has been added yet." />

      {canWrite && (
        <form onSubmit={onSubmit} className="card mt-6 gap-4 p-4">
          <h3 className="text-[14px] font-medium text-text">{formLabel}</h3>

          <div className="field">
            <label htmlFor={`${id}-title`}>
              Title <span className="font-normal text-muted">(optional)</span>
            </label>
            <input
              id={`${id}-title`}
              type="text"
              value={heading}
              onChange={(e) => setHeading(e.target.value)}
              className="input"
            />
          </div>

          <div className="field">
            <label htmlFor={`${id}-body`}>
              What would you like the next teacher to know?
            </label>
            <textarea
              id={`${id}-body`}
              rows={4}
              required
              value={body}
              onChange={(e) => setBody(e.target.value)}
              className="input"
            />
          </div>

          <button
            type="submit"
            disabled={pending || body.trim() === ''}
            className="btn btn-primary self-start"
          >
            {pending ? 'Saving…' : 'Add to the passport'}
          </button>

          <p aria-live="polite" className="text-[13px] text-muted">
            {saved && !pending && 'Saved. It now appears above.'}
          </p>
          {error && (
            <p role="alert" className="text-[13px] text-red-300">
              {error}
            </p>
          )}
        </form>
      )}
    </Section>
  );
}
