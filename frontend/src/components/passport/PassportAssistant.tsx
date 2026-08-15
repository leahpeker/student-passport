import {
  forwardRef,
  useImperativeHandle,
  useRef,
  useState,
  type FormEvent,
} from 'react';
import { askQuestion } from '../../api/client';
import type { Answer, Student } from '../../api/types';
import type { Pulse } from '../../lib/pulse';
import { metricText, toneDot, toneText } from './tone';

export interface AssistantHandle {
  /** Open the panel and, if a prompt is given, ask it straight away. */
  ask: (prompt?: string) => void;
}

interface Message {
  id: number;
  role: 'user' | 'assistant';
  text: string;
  pending?: boolean;
  citedCount?: number;
}

const SUGGESTIONS = [
  'Draft a check-in plan',
  'Draft a message to their guardian',
  'What changed since last week?',
];

let messageId = 0;

/**
 * The passport's AI agent, docked bottom-right the way a help widget is. It
 * opens from the pulse — the pulse summary sits at the top of the thread as the
 * opening context — and every answer is drawn from the student's records.
 */
export const PassportAssistant = forwardRef<
  AssistantHandle,
  {
    student: Student;
    pulse: Pulse;
    onAnswered: (answer: Answer) => void;
  }
>(function PassportAssistant({ student, pulse, onAnswered }, ref) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState('');
  const bodyRef = useRef<HTMLDivElement>(null);

  const scrollDown = () => {
    requestAnimationFrame(() => {
      if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    });
  };

  async function send(prompt: string) {
    const asked = prompt.trim();
    if (!asked) return;
    const pendingId = ++messageId;
    setMessages((prev) => [
      ...prev,
      { id: ++messageId, role: 'user', text: asked },
      { id: pendingId, role: 'assistant', text: '', pending: true },
    ]);
    scrollDown();
    try {
      const answer = await askQuestion(student.id, asked);
      onAnswered(answer);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === pendingId
            ? {
                ...m,
                pending: false,
                text: answer.answer,
                citedCount: answer.cited_record_ids.length,
              }
            : m,
        ),
      );
    } catch {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === pendingId
            ? { ...m, pending: false, text: 'That could not be answered. Try again.' }
            : m,
        ),
      );
    } finally {
      scrollDown();
    }
  }

  useImperativeHandle(ref, () => ({
    ask(prompt?: string) {
      setOpen(true);
      if (prompt) void send(prompt);
    },
  }));

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    const asked = draft.trim();
    if (!asked) return;
    setDraft('');
    void send(asked);
  }

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="btn btn-primary fixed right-5 bottom-5 z-40 rounded-full bg-surface px-4 py-3 elev-md"
      >
        ✦ Ask about {student.first_name}
      </button>
    );
  }

  return (
    <section
      aria-label={`Assistant for ${student.name}`}
      className="fixed right-5 bottom-5 z-40 flex h-[500px] w-[min(380px,calc(100vw-2.5rem))] flex-col overflow-hidden rounded-lg bg-surface elev-lg"
    >
      <header className="flex items-center gap-2.5 border-b border-divider px-4 py-3">
        <span aria-hidden="true" className="text-accent">
          ✦
        </span>
        <div className="flex-1">
          <p className="text-[13px] font-medium text-text">Passport assistant</p>
          <p className="text-[10.5px] text-muted">
            Grounded in {student.first_name}'s records · cites sources
          </p>
        </div>
        <button
          type="button"
          onClick={() => setOpen(false)}
          aria-label="Close the assistant"
          className="btn btn-secondary px-2 py-1 text-[13px]"
        >
          ✕
        </button>
      </header>

      <div ref={bodyRef} className="flex-1 space-y-3 overflow-y-auto p-3.5">
        <PulseOpening pulse={pulse} />
        {messages.length === 0 && (
          <p className="rounded-lg bg-[var(--surface-well)] px-3 py-2.5 text-[12px] text-text/80">
            Ask me anything about {student.first_name} — I'll answer from the
            passport and point to the records behind it.
          </p>
        )}
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}
      </div>

      <div className="flex flex-wrap gap-1.5 px-3.5 pb-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => void send(s)}
            className="tag tag-outline cursor-pointer"
          >
            {s}
          </button>
        ))}
      </div>

      <form onSubmit={onSubmit} className="flex items-end gap-2 border-t border-divider p-2.5">
        <label htmlFor="assistant-input" className="sr-only">
          Ask about {student.first_name}
        </label>
        <textarea
          id="assistant-input"
          rows={1}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              onSubmit(e);
            }
          }}
          placeholder={`Ask about ${student.first_name}…`}
          className="input min-h-9 flex-1 resize-none"
        />
        <button type="submit" disabled={draft.trim() === ''} className="btn btn-primary">
          Send
        </button>
      </form>
    </section>
  );
});

/** The pulse detail, shown once at the top of the thread as opening context. */
function PulseOpening({ pulse }: { pulse: Pulse }) {
  return (
    <div className="rounded-lg border border-divider bg-[var(--surface-well)] p-3">
      <p className={`flex items-center gap-2 text-[12.5px] font-medium ${toneText[pulse.tone]}`}>
        <span aria-hidden="true" className={`h-2 w-2 rounded-full ${toneDot[pulse.tone]}`} />
        Pulse — {pulse.headline}
      </p>
      <Kicker>Why</Kicker>
      <p className="text-[11.5px] leading-relaxed text-text/80">{pulse.why}</p>
      <Kicker>Since your last visit · {pulse.since.asOf}</Kicker>
      <ul className="space-y-0.5">
        {pulse.since.changes.map((c, i) => (
          <li key={i} className="flex gap-2 text-[11.5px] text-text/80">
            <span aria-hidden="true" className={`font-semibold ${toneText[pulse.tone]}`}>
              {c.direction === 'up' ? '↑' : c.direction === 'down' ? '↓' : '+'}
            </span>
            {c.text}
          </li>
        ))}
      </ul>
      <Kicker>In context</Kicker>
      <ul className="flex flex-wrap gap-x-3 gap-y-1">
        {pulse.context.map((c) => (
          <li key={c.label} className="text-[11px] text-muted">
            {c.label}: <span className={metricText[c.tone]}>{c.value}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Kicker({ children }: { children: React.ReactNode }) {
  return (
    <p className="mt-2.5 mb-1 text-[9px] font-semibold tracking-[0.08em] text-muted uppercase">
      {children}
    </p>
  );
}

function MessageBubble({ message }: { message: Message }) {
  if (message.role === 'user') {
    return (
      <p className="ml-auto max-w-[85%] rounded-lg rounded-br-sm bg-accent-800 px-3 py-2 text-[12px] text-accent-100">
        {message.text}
      </p>
    );
  }
  return (
    <div className="max-w-[85%] rounded-lg rounded-bl-sm border border-divider bg-bg px-3 py-2">
      {message.pending ? (
        <p className="text-[12px] text-muted">Thinking…</p>
      ) : (
        <>
          <p className="text-[12px] leading-relaxed text-text/85">{message.text}</p>
          {message.citedCount != null && (
            <p className="mt-1.5 text-[10.5px] text-muted">
              Answered from {message.citedCount} records · saved to the passport
            </p>
          )}
        </>
      )}
    </div>
  );
}
