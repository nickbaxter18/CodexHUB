import { mergeCursorRules } from '../src/cursor/adaptor';
import type { AgentGuidelines } from '../src/shared/types';

const baseGuidelines: AgentGuidelines = {
  environment: ['pnpm install'],
  testing: ['pnpm test'],
  coding: ['use named exports'],
  logging: ['structured logger'],
  pullRequests: ['reference checks'],
};

describe('mergeCursorRules', () => {
  it('combines Cursor rules with project guidelines without losing defaults', () => {
    const merged = mergeCursorRules(baseGuidelines, {
      environment: ['pnpm setup'],
      testing: ['pnpm typecheck'],
    });

    expect(merged.environment).toEqual(['pnpm install', 'pnpm setup']);
    expect(merged.testing).toEqual(['pnpm test', 'pnpm typecheck']);
    expect(merged.coding).toEqual(baseGuidelines.coding);
  });

  it('deduplicates and sanitises merged rules', () => {
    const merged = mergeCursorRules(baseGuidelines, {
      environment: ['  pnpm install  ', ''],
      logging: ['structured logger', 'add breadcrumbs'],
    });

    expect(merged.environment).toEqual(['pnpm install']);
    expect(merged.logging).toEqual(['structured logger', 'add breadcrumbs']);
  });
});
