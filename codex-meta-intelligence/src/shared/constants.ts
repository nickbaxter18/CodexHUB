export const DEFAULT_AGENT_TIMEOUT_MS = 5 * 60 * 1000;
export const DEFAULT_CONCURRENCY = 2;
export const PIPELINE_STAGES = [
  'draft',
  'audit',
  'refinement',
  'elevation',
  'delivery',
  'deploy',
] as const;

export const QA_SEVERITY_ORDER: Record<'info' | 'warning' | 'error', number> = {
  info: 0,
  warning: 1,
  error: 2,
};

export const DEFAULT_CACHE_CAPACITY = 256;
export const DEFAULT_CACHE_TTL_MS = 10 * 60 * 1000;
