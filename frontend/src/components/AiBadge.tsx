/**
 * Marks a student with a `cognitive_analysis` record on file. Uses the
 * accent's low-alpha-fill pattern (see `passport/tone.ts`) so it reads the
 * same in both theme variants.
 */
export function AiBadge() {
  return (
    <span
      aria-label="AI usage portfolio on file"
      title="AI usage portfolio on file"
      className="inline-flex h-4 shrink-0 items-center rounded-[4px] border border-accent/40 bg-accent/10 px-1 text-[9px] font-semibold tracking-[0.02em] text-accent"
    >
      AI
    </span>
  );
}
