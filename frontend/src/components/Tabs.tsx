import { useRef, type ReactNode } from 'react';

export interface TabItem {
  id: string;
  label: string;
  /** Secondary line under the label, e.g. a roster count. */
  hint?: string;
}

/**
 * A real ARIA tab list: arrow keys move between tabs, Home and End jump to the
 * ends, and only the selected tab is in the tab order.
 */
export function Tabs({
  label,
  tabs,
  activeId,
  onChange,
  children,
}: {
  label: string;
  tabs: TabItem[];
  activeId: string;
  onChange: (id: string) => void;
  children: ReactNode;
}) {
  const listRef = useRef<HTMLDivElement>(null);

  function onKeyDown(event: React.KeyboardEvent<HTMLDivElement>) {
    const offset =
      event.key === 'ArrowRight' || event.key === 'ArrowDown'
        ? 1
        : event.key === 'ArrowLeft' || event.key === 'ArrowUp'
          ? -1
          : 0;
    let next = -1;
    if (offset !== 0) {
      const current = tabs.findIndex((t) => t.id === activeId);
      next = (current + offset + tabs.length) % tabs.length;
    } else if (event.key === 'Home') {
      next = 0;
    } else if (event.key === 'End') {
      next = tabs.length - 1;
    }
    if (next < 0) return;
    event.preventDefault();
    const tab = tabs[next];
    onChange(tab.id);
    listRef.current
      ?.querySelector<HTMLButtonElement>(`#tab-${CSS.escape(tab.id)}`)
      ?.focus();
  }

  return (
    <div>
      <div
        ref={listRef}
        role="tablist"
        aria-label={label}
        onKeyDown={onKeyDown}
        className="flex flex-wrap gap-2 border-b border-slate-200 pb-px"
      >
        {tabs.map((tab) => {
          const selected = tab.id === activeId;
          return (
            <button
              key={tab.id}
              id={`tab-${tab.id}`}
              type="button"
              role="tab"
              aria-selected={selected}
              aria-controls={`panel-${tab.id}`}
              tabIndex={selected ? 0 : -1}
              onClick={() => onChange(tab.id)}
              className={`-mb-px rounded-t-md border-b-2 px-4 py-2.5 text-left text-sm transition-colors ${
                selected
                  ? 'border-indigo-600 bg-white font-semibold text-indigo-700'
                  : 'border-transparent font-medium text-slate-600 hover:border-slate-300 hover:text-slate-900'
              }`}
            >
              <span className="block">{tab.label}</span>
              {tab.hint && (
                <span className="block text-xs font-normal text-slate-500">
                  {tab.hint}
                </span>
              )}
            </button>
          );
        })}
      </div>
      <div
        id={`panel-${activeId}`}
        role="tabpanel"
        aria-labelledby={`tab-${activeId}`}
        tabIndex={0}
        className="pt-6 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-indigo-600"
      >
        {children}
      </div>
    </div>
  );
}
