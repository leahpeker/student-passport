import type { ReactNode } from 'react';

export interface ChartTable {
  headers: string[];
  rows: (string | number)[][];
}

/**
 * A chart with a text alternative.
 *
 * The drawing itself is hidden from assistive technology — charts pass their
 * `accessibilityLayer={false}` so nothing inside is focusable — and the same
 * numbers are published as a real table plus a written summary. Colour is
 * never the only way to read a series: every chart pairs it with a label, a
 * line style or a printed value.
 */
export function ChartFigure({
  caption,
  summary,
  table,
  children,
}: {
  /** What the chart shows. */
  caption: string;
  /** The trend in words, for anyone who cannot see the drawing. */
  summary: ReactNode;
  table: ChartTable;
  children: ReactNode;
}) {
  return (
    <figure className="m-0">
      <div aria-hidden="true" className="h-64 w-full">
        {children}
      </div>
      <figcaption className="mt-3 text-sm leading-relaxed text-slate-600">
        <span className="font-medium text-slate-900">{caption}</span> {summary}
      </figcaption>
      <details className="mt-3 rounded-lg border border-slate-200 bg-slate-50 px-4 py-2">
        <summary className="cursor-pointer text-sm font-medium text-slate-700">
          Show these figures as a table
        </summary>
        <div className="overflow-x-auto pb-2">
          <table className="mt-3 w-full border-collapse text-sm">
            <caption className="sr-only">{caption}</caption>
            <thead>
              <tr>
                {table.headers.map((header) => (
                  <th
                    key={header}
                    scope="col"
                    className="border-b border-slate-300 px-3 py-2 text-left font-semibold text-slate-900"
                  >
                    {header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {table.rows.map((row, i) => (
                <tr key={i}>
                  {row.map((cell, j) =>
                    j === 0 ? (
                      <th
                        key={j}
                        scope="row"
                        className="border-b border-slate-200 px-3 py-2 text-left font-medium text-slate-700"
                      >
                        {cell}
                      </th>
                    ) : (
                      <td
                        key={j}
                        className="border-b border-slate-200 px-3 py-2 text-slate-600 tabular-nums"
                      >
                        {cell}
                      </td>
                    ),
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </figure>
  );
}
