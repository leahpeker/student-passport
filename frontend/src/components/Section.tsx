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
      className="elev-sm rounded-lg bg-surface p-[19px]"
    >
      <h2
        id={`${id}-heading`}
        className="text-[18px] font-medium tracking-[-0.015em] text-text"
      >
        {title}
      </h2>
      {lead && (
        <p className="mt-2 text-[12.5px] leading-relaxed text-muted">{lead}</p>
      )}
      <div className="mt-5">{children}</div>
    </section>
  );
}
