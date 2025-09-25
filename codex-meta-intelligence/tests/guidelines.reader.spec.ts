import { mkdtempSync, mkdirSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

import { AgentGuidelineReader } from '../src/agent/reader';

const createAgentsFile = (): { root: string; nested: string } => {
  const directory = mkdtempSync(path.join(tmpdir(), 'guidelines-reader-'));
  mkdirSync(path.join(directory, 'src', 'feature'), { recursive: true });
  writeFileSync(
    path.join(directory, 'AGENTS.md'),
    `# Root\n\n## Environment Setup\n1. Install pnpm\n2. Enable corepack\n\n## Testing\n\n- pnpm test --filter codex-meta-intelligence\n`
  );
  const nested = path.join(directory, 'src', 'feature');
  writeFileSync(
    path.join(nested, 'AGENTS.md'),
    `# Nested\n\n## Environment Setup\n- Use Node 18\n\n## Testing\n\n\`pnpm test\`\n\n## Coding\n\n\`\`\`bash\npnpm lint\n\`\`\``
  );
  return { root: directory, nested };
};

describe('AgentGuidelineReader', () => {
  it('merges bullet, ordered and fenced entries while preserving order', async () => {
    const { root, nested } = createAgentsFile();
    const reader = new AgentGuidelineReader(root);
    const guidelines = await reader.mergeGuidelines(nested);

    expect(guidelines.environment).toEqual([
      'Install pnpm',
      'Enable corepack',
      'Use Node 18',
    ]);
    expect(guidelines.testing).toContain('pnpm test --filter codex-meta-intelligence');
    expect(guidelines.testing).toContain('`pnpm test`');
    expect(guidelines.coding[0]).toBe('pnpm lint');
  });
});
