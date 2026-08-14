import type { ReactNode } from 'react';

export function Section({
  id,
  title,
  lead,
  children,
}: {
  id: string;
  title: string;
  lead?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section
      id={id}
      aria-labelledby={`${id}-heading`}
      className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
    >
      <h2
        id={`${id}-heading`}
        className="text-lg font-semibold tracking-tight text-slate-900"
      >
        {title}
      </h2>
      {lead && <p className="mt-3 leading-relaxed text-slate-600">{lead}</p>}
      <div className="mt-5">{children}</div>
    </section>
  );
}
