import { mkdtemp, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';

import {
  enforceCursorIntegration,
  getAutoInvoker,
  requireCursorAgent,
  startCursorAutoInvocation,
  stopCursorAutoInvocation,
  validateCursorCompliance,
} from '../src/cursor/index';
import {
  getKnowledgeEntries,
  startKnowledgeAutoLoading,
  stopKnowledgeAutoLoading,
} from '../src/knowledge/auto-loader';
import {
  startBrainBlocksIntegration,
  stopBrainBlocksIntegration,
} from '../src/knowledge/brain-blocks-integration';
import { startMobileApp, stopMobileApp } from '../src/mobile/mobile-app';

const createKnowledgeFile = async (): Promise<string> => {
  const directory = await mkdtemp(path.join(tmpdir(), 'cmi-knowledge-'));
  const filePath = path.join(directory, 'blocks.ndjson');
  const content = [
    JSON.stringify({
      id: 'brain-1',
      content: '# Section\nCursor integration knowledge entry',
      metadata: {
        author: 'test',
        timestamp: new Date().toISOString(),
        tags: ['section:runtime', 'cursor'],
        citations: [],
        source: 'test-suite',
        reliabilityScore: 0.9,
      },
    }),
  ].join('\n');
  await writeFile(filePath, content, 'utf8');
  return filePath;
};

describe('Cursor integration runtime', () => {
  const originalEnv = {
    CURSOR_API_URL: process.env.CURSOR_API_URL,
    CURSOR_API_KEY: process.env.CURSOR_API_KEY,
    CURSOR_STRICT_MODE: process.env.CURSOR_STRICT_MODE,
    KNOWLEDGE_AUTO_LOAD: process.env.KNOWLEDGE_AUTO_LOAD,
    KNOWLEDGE_NDJSON_PATHS: process.env.KNOWLEDGE_NDJSON_PATHS,
  };

  beforeAll(() => {
    process.env.CURSOR_API_URL = process.env.CURSOR_API_URL ?? 'https://api.cursor.sh';
    process.env.CURSOR_API_KEY = process.env.CURSOR_API_KEY ?? 'test-key';
    process.env.CURSOR_STRICT_MODE = 'false';
    process.env.KNOWLEDGE_AUTO_LOAD = 'true';
  });

  // codespell:ignore afterEach
  afterEach(async () => {
    stopCursorAutoInvocation();
    await stopKnowledgeAutoLoading();
    stopBrainBlocksIntegration();
    stopMobileApp();
  });

  // codespell:ignore afterAll
  afterAll(() => {
    process.env.CURSOR_API_URL = originalEnv.CURSOR_API_URL;
    process.env.CURSOR_API_KEY = originalEnv.CURSOR_API_KEY;
    process.env.CURSOR_STRICT_MODE = originalEnv.CURSOR_STRICT_MODE;
    process.env.KNOWLEDGE_AUTO_LOAD = originalEnv.KNOWLEDGE_AUTO_LOAD;
    process.env.KNOWLEDGE_NDJSON_PATHS = originalEnv.KNOWLEDGE_NDJSON_PATHS;
  });

  it('maintains full Cursor compliance after startup', async () => {
    const knowledgeFile = await createKnowledgeFile();
    process.env.KNOWLEDGE_NDJSON_PATHS = knowledgeFile;

    await startKnowledgeAutoLoading([knowledgeFile], 50);
    await startBrainBlocksIntegration();
    await startMobileApp();

    const workspace = await mkdtemp(path.join(tmpdir(), 'cmi-workspace-'));
    await startCursorAutoInvocation([workspace]);

    const wrapped = requireCursorAgent('FRONTEND')(() => 'ready');
    expect(wrapped()).toBe('ready');

    const targetFile = path.join(workspace, 'example.ts');
    await writeFile(targetFile, 'export const example = 1;');
    await delay(100);

    const invoker = getAutoInvoker();
    expect(invoker).toBeDefined();
    expect(invoker?.getTriggeredFiles()).toContain(targetFile);

    const entries = await getKnowledgeEntries();
    expect(entries.length).toBeGreaterThan(0);

    const report = await validateCursorCompliance();
    expect(report.compliance).toBeCloseTo(1, 5);
    await expect(enforceCursorIntegration()).resolves.toBeUndefined();
  });
});
