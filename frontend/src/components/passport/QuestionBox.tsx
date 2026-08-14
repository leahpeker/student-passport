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
        <div className="field">
          <label htmlFor="question">Your question</label>
          <div className="flex items-start gap-2">
            <textarea
              id="question"
              name="question"
              rows={3}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="What helps this student most in the morning?"
              className="input"
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
                className={`btn shrink-0 p-2.5 ${
                  dictation.listening
                    ? 'border-red-500 bg-red-950/40 text-red-300'
                    : 'btn-secondary'
                }`}
              >
                <MicIcon active={dictation.listening} />
              </button>
            )}
          </div>
        </div>
        {dictation.listening && (
          <p role="status" className="mt-2 text-[13px] text-red-300">
            Listening. Speak your question, then press the microphone again.
          </p>
        )}

        <ul className="mt-3 flex flex-wrap gap-2">
          {SUGGESTIONS.map((suggestion) => (
            <li key={suggestion}>
              <button
                type="button"
                onClick={() => setQuestion(suggestion)}
                className="tag tag-outline cursor-pointer"
              >
                {suggestion}
              </button>
            </li>
          ))}
        </ul>

        <button
          type="submit"
          disabled={pending || question.trim() === ''}
          className="btn btn-primary mt-4"
        >
          {pending ? 'Asking…' : 'Ask'}
        </button>
      </form>

      {error && (
        <p
          role="alert"
          className="mt-4 rounded-md bg-red-950/40 px-3 py-2 text-[13px] text-red-300"
        >
          {error}
        </p>
      )}

      <div aria-live="polite" className="mt-6 space-y-4">
        {answers.map((answer) => (
          <article
            key={answer.record.id}
            className="rounded-lg p-4"
            style={{ background: 'var(--surface-well)' }}
          >
            <h3 className="text-[12.5px] font-medium text-accent">
              {answer.question}
            </h3>
            <p className="mt-2 text-[12.5px] leading-relaxed text-text/80">
              {answer.answer}
            </p>
            <p className="mt-3 text-[11px] text-muted">
              Answered from {answer.cited_record_ids.length} records. Saved to the
              passport.
            </p>
          </article>
        ))}
      </div>
    </Section>
  );
}
