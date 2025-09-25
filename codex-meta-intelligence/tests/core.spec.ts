import { ContextFabric } from '../src/context/fabric';
import { MacroOrchestrator } from '../src/macro/index';
import { KnowledgeService } from '../src/knowledge/index';
import { QAEngine } from '../src/qa/index';
import { ForesightEngine } from '../src/foresight/index';
import { MetaAgent } from '../src/metaagent/index';
import type { MacroContext } from '../src/shared/types';
import type { JsonValue } from '../src/shared/utils';

const createSamplePacket = () => {
  const fabric = new ContextFabric();
  return fabric.ingest('test', 'Sample context packet for QA checks.', { sensitivity: 'public' });
};

const toJsonValue = (value: unknown): JsonValue => JSON.parse(JSON.stringify(value)) as JsonValue;

describe('Codex Meta-Intelligence Stage 1', () => {
  it('stores and queries knowledge blocks', () => {
    const service = new KnowledgeService();
    const block = service.storeBlock({
      id: 'kb-1',
      content: 'The system executes macros and agents cooperatively.',
      metadata: {
        author: 'system',
        timestamp: new Date().toISOString(),
        tags: ['architecture'],
        citations: [],
        source: 'test',
        reliabilityScore: 0.9,
      },
    });
    const response = service.queryKnowledge({ keywords: ['macros'], limit: 5 });
    expect(response.blocks[0]?.block.id).toBe(block.id);
  });

  it('upserts existing knowledge blocks without duplicating metadata', () => {
    const service = new KnowledgeService();
    const timestamp = new Date().toISOString();
    service.storeBlock({
      id: 'kb-upsert',
      content: 'Initial content',
      metadata: {
        author: 'system',
        timestamp,
        tags: ['initial'],
        citations: ['doc-1'],
        source: 'test',
        reliabilityScore: 0.5,
      },
    });
    const updated = service.upsertBlock({
      id: 'kb-upsert',
      content: 'Initial content with refinements',
      metadata: {
        author: 'system',
        timestamp,
        tags: ['refined'],
        citations: ['doc-2'],
        source: 'test',
        reliabilityScore: 0.8,
      },
    });
    expect(updated.metadata.tags.sort()).toEqual(['initial', 'refined']);
    expect(updated.metadata.citations.sort()).toEqual(['doc-1', 'doc-2']);
    expect(updated.metadata.reliabilityScore).toBe(0.8);
  });

  it('runs macros through the execution pipeline', async () => {
    const orchestrator = new MacroOrchestrator();
    const packet = createSamplePacket();
    const context: MacroContext = {
      taskId: 'task-1',
      operatorId: 'operator',
      input: {},
      metadata: { contextPackets: toJsonValue([packet]) },
      guidelines: {
        environment: ['pnpm install'],
        testing: ['pnpm test'],
        coding: [],
        logging: [],
        pullRequests: [],
      },
    };
    const result = await orchestrator.runMacro('full-pipeline', context);
    expect(result.success).toBe(true);
    expect(result.stageResults).toHaveLength(4);
  });

  it('executes QA checks with combined engines', () => {
    const engine = new QAEngine();
    const issues = engine.runQA({
      aesthetic: {
        palette: [
          { name: 'Primary', contrastRatio: 4.6 },
          { name: 'Secondary', contrastRatio: 4.8 },
        ],
        typographyScale: [1, 1.25, 1.6],
        motionDensity: 0.3,
      },
      technical: { lintErrors: 0, testFailures: 0, coverage: 0.9 },
      narrative: { tone: 'empathetic', coherenceScore: 0.9, fairnessScore: 0.95 },
    });
    expect(issues.success).toBe(true);
  });

  it('provides foresight predictions and risk assessments', () => {
    const engine = new ForesightEngine();
    const forecast = engine.predict({
      taskId: 'task-2',
      durations: [100, 120, 110],
      qaIssues: [0, 1, 0],
    });
    expect(forecast.confidence).toBeGreaterThan(0.4);
    const risk = engine.assessRisk('task-2', 1, 2, 2);
    expect(risk.level).toBe('low');
  });

  it('processes tasks via the meta-agent', async () => {
    const metaAgent = new MetaAgent();
    const packet = createSamplePacket();
    const context: MacroContext = {
      taskId: 'meta-task',
      operatorId: 'operator',
      input: {},
      metadata: { contextPackets: toJsonValue([packet]) },
      guidelines: {
        environment: [],
        testing: [],
        coding: [],
        logging: [],
        pullRequests: [],
      },
    };
    const taskId = metaAgent.enqueueTask(
      {
        macroName: 'full-pipeline',
        input: {},
        priority: 5,
        owner: 'operator',
      },
      context
    );
    expect(taskId).toBeTruthy();
    await new Promise((resolve) => setTimeout(resolve, 50));
    const state = metaAgent.getState();
    expect(state.completed.some((result) => result.taskId === context.taskId)).toBe(true);
  });
});
