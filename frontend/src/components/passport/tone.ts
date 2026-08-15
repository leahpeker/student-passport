/**
 * How each pulse colour is drawn. Kept in one place so the nav dots, the pulse
 * hero and the assistant all read the same red / amber / green.
 *
 * Dark is the app's native mode; these use the -500 family plus low-alpha
 * fills so the same classes stay legible in the light variant too.
 */

import type { PulseTone, Trend } from '../../lib/pulse';

/** Solid dot, for roster rows and the status light. */
export const toneDot: Record<PulseTone, string> = {
  red: 'bg-red-500',
  amber: 'bg-amber-500',
  green: 'bg-emerald-500',
};

/** Text/accent colour. */
export const toneText: Record<PulseTone, string> = {
  red: 'text-red-500',
  amber: 'text-amber-500',
  green: 'text-emerald-500',
};

/** Card surface — tinted fill plus a matching border. */
export const toneCard: Record<PulseTone, string> = {
  red: 'border-red-500/40 bg-red-500/10',
  amber: 'border-amber-500/40 bg-amber-500/10',
  green: 'border-emerald-500/40 bg-emerald-500/10',
};

/** Short label under the status light. */
export const toneLabel: Record<PulseTone, string> = {
  red: 'Needs attention',
  amber: 'Watch',
  green: 'On track',
};

/** How a context metric reads, independent of the overall tone. */
export const metricText: Record<'good' | 'bad' | 'neutral', string> = {
  good: 'text-emerald-500',
  bad: 'text-red-500',
  neutral: 'text-muted',
};

export function trendArrow(trend: Trend): string {
  return trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→';
}
