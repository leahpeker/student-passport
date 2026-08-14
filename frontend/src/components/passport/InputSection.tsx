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
        <form
          onSubmit={onSubmit}
          className="mt-6 rounded-lg border border-slate-200 bg-slate-50 p-4"
        >
          <h3 className="font-medium text-slate-900">{formLabel}</h3>

          <label
            htmlFor={`${id}-title`}
            className="mt-4 block text-sm font-medium text-slate-700"
          >
            Title <span className="font-normal text-slate-500">(optional)</span>
          </label>
          <input
            id={`${id}-title`}
            type="text"
            value={heading}
            onChange={(e) => setHeading(e.target.value)}
            className="mt-1.5 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-900 focus:border-indigo-600"
          />

          <label
            htmlFor={`${id}-body`}
            className="mt-4 block text-sm font-medium text-slate-700"
          >
            What would you like the next teacher to know?
          </label>
          <textarea
            id={`${id}-body`}
            rows={4}
            required
            value={body}
            onChange={(e) => setBody(e.target.value)}
            className="mt-1.5 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-900 focus:border-indigo-600"
          />

          <button
            type="submit"
            disabled={pending || body.trim() === ''}
            className="mt-4 rounded-md bg-indigo-700 px-4 py-2 font-medium text-white hover:bg-indigo-800 disabled:opacity-50"
          >
            {pending ? 'Saving…' : 'Add to the passport'}
          </button>

          <p aria-live="polite" className="mt-3 text-sm text-slate-600">
            {saved && !pending && 'Saved. It now appears above.'}
          </p>
          {error && (
            <p role="alert" className="mt-1 text-sm text-red-800">
              {error}
            </p>
          )}
        </form>
      )}
    </Section>
  );
}
