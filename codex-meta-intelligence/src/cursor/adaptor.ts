import type { AgentGuidelines } from '../shared/types.js';

interface CursorRules {
  environment?: string[];
  testing?: string[];
  coding?: string[];
  logging?: string[];
  pullRequests?: string[];
}

const createBaseline = (guidelines: AgentGuidelines): AgentGuidelines => ({
  environment: [...guidelines.environment],
  testing: [...guidelines.testing],
  coding: [...guidelines.coding],
  logging: [...guidelines.logging],
  pullRequests: [...guidelines.pullRequests],
});

const sanitiseValues = (values: string[]): string[] => {
  const unique = new Set<string>();
  for (const value of values) {
    if (typeof value !== 'string') continue;
    const trimmed = value.trim();
    if (!trimmed) continue;
    unique.add(trimmed);
  }
  return Array.from(unique);
};

export const mergeCursorRules = (
  guidelines: AgentGuidelines,
  cursorRules: CursorRules
): AgentGuidelines => {
  const result = createBaseline(guidelines);
  for (const key of Object.keys(cursorRules) as Array<keyof CursorRules>) {
    const updates = cursorRules[key];
    if (!updates?.length) continue;
    const targetKey = key as keyof AgentGuidelines;
    const combined = [...result[targetKey], ...updates];
    result[targetKey] = sanitiseValues(combined);
  }
  return result;
};
