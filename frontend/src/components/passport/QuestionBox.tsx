import { useCallback, useState } from 'react';
import { askQuestion } from '../../api/client';
import type { Answer, Student } from '../../api/types';
import { useDictation } from '../../lib/speech';
import { Section } from '../Section';

const SUGGESTIONS = [
  'When is this student most engaged?',
  'How has their performance moved this year?',
  'Is there a pattern in the behaviour entries?',
  'What should I know before their first lesson with me?',
];

function MicIcon({ active }: { active: boolean }) {
  return (
    <svg
      viewBox="0 0 24 24"
      className="h-5 w-5"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      aria-hidden="true"
    >
      <rect x="9" y="3" width="6" height="11" rx="3" />
      <path d="M5 11a7 7 0 0 0 14 0M12 18v3" />
      {active && <circle cx="19" cy="5" r="2.5" fill="currentColor" stroke="none" />}
    </svg>
  );
}

export function QuestionBox({
  student,
  onAnswered,
}: {
  student: Student;
  onAnswered: (answer: Answer) => void;
}) {
  const [question, setQuestion] = useState('');
  const [answers, setAnswers] = useState<Answer[]>([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const appendTranscript = useCallback((text: string) => {
    setQuestion((current) => (current ? `${current} ${text}` : text));
  }, []);
  const dictation = useDictation(appendTranscript);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    const asked = question.trim();
    if (!asked) return;
    setPending(true);
    setError(null);
    try {
      const answer = await askQuestion(student.id, asked);
      setAnswers((current) => [answer, ...current]);
      onAnswered(answer);
      setQuestion('');
    } catch {
      setError('That question could not be answered. Try again.');
    } finally {
      setPending(false);
    }
  }

  return (
    <Section
      id="ask"
      title="Ask about this student"
      lead={`Questions are answered from ${student.first_name}'s records, and each exchange is kept in the passport so the next person can see what was asked.`}
    >
      <form onSubmit={onSubmit}>
        <label
          htmlFor="question"
          className="block text-sm font-medium text-slate-700"
        >
          Your question
        </label>
        <div className="mt-1.5 flex items-start gap-2">
          <textarea
            id="question"
            name="question"
            rows={3}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="What helps this student most in the morning?"
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-slate-900 placeholder:text-slate-400 focus:border-indigo-600"
          />
          {dictation.supported && (
            <button
              type="button"
              aria-pressed={dictation.listening}
              aria-label={
                dictation.listening
                  ? 'Stop dictating your question'
                  : 'Dictate your question'
              }
              onClick={dictation.listening ? dictation.stop : dictation.start}
              className={`shrink-0 rounded-md border p-2.5 ${
                dictation.listening
                  ? 'border-red-500 bg-red-50 text-red-700'
                  : 'border-slate-300 text-slate-600 hover:border-slate-400 hover:bg-slate-50'
              }`}
            >
              <MicIcon active={dictation.listening} />
            </button>
          )}
        </div>
        {dictation.listening && (
          <p role="status" className="mt-2 text-sm text-red-700">
            Listening. Speak your question, then press the microphone again.
          </p>
        )}

        <ul className="mt-3 flex flex-wrap gap-2">
          {SUGGESTIONS.map((suggestion) => (
            <li key={suggestion}>
              <button
                type="button"
                onClick={() => setQuestion(suggestion)}
                className="rounded-full border border-slate-200 px-3 py-1 text-sm text-slate-600 hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-800"
              >
                {suggestion}
              </button>
            </li>
          ))}
        </ul>

        <button
          type="submit"
          disabled={pending || question.trim() === ''}
          className="mt-4 rounded-md bg-indigo-700 px-4 py-2 font-medium text-white hover:bg-indigo-800 disabled:opacity-50"
        >
          {pending ? 'Asking…' : 'Ask'}
        </button>
      </form>

      {error && (
        <p
          role="alert"
          className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800"
        >
          {error}
        </p>
      )}

      <div aria-live="polite" className="mt-6 space-y-4">
        {answers.map((answer) => (
          <article
            key={answer.record.id}
            className="rounded-lg border border-indigo-200 bg-indigo-50/60 p-4"
          >
            <h3 className="font-medium text-slate-900">{answer.question}</h3>
            <p className="mt-2 leading-relaxed text-slate-700">{answer.answer}</p>
            <p className="mt-3 text-sm text-slate-500">
              Answered from {answer.cited_record_ids.length} records. Saved to the
              passport.
            </p>
          </article>
        ))}
      </div>
    </Section>
  );
}
