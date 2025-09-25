import { MacroOrchestrator } from '../src/macro/index';
import type { MacroDefinition, MacroContext } from '../src/shared/types';
import { AgentRole } from '../src/shared/types';
import { ContextFabric } from '../src/context/fabric';

const createContext = (): MacroContext => {
  const fabric = new ContextFabric();
  return {
    taskId: 'task',
    operatorId: 'operator',
    input: {},
    metadata: {
      contextPackets: JSON.parse(
        JSON.stringify([fabric.ingest('source', 'Example', { sensitivity: 'public' })])
      ),
    },
    guidelines: {
      environment: [],
      testing: [],
      coding: [],
      logging: [],
      pullRequests: [],
    },
  };
};

describe('MacroOrchestrator advanced behaviour', () => {
  it('detects fallback cycles to avoid infinite recursion', async () => {
    const definitions: MacroDefinition[] = [
      {
        name: 'unstable',
        description: 'Always falls back',
        qualityThreshold: 0.2,
        fallbackMacro: 'rescue',
        stages: [
          {
            id: 'draft',
            name: 'Draft',
            description: 'Frontend draft without context',
            agentRole: AgentRole.FRONTEND,
            retryLimit: 0,
            continueOnError: false,
          },
        ],
      },
      {
        name: 'rescue',
        description: 'Falls back to unstable',
        qualityThreshold: 0.2,
        fallbackMacro: 'unstable',
        stages: [
          {
            id: 'draft-rescue',
            name: 'Draft Rescue',
            description: 'Frontend draft without context',
            agentRole: AgentRole.FRONTEND,
            retryLimit: 0,
            continueOnError: false,
          },
        ],
      },
    ];
    const registry = new Map(definitions.map((definition) => [definition.name, definition]));
    const orchestrator = new MacroOrchestrator(registry);
    await expect(orchestrator.runMacro('unstable', {
      ...createContext(),
      metadata: { contextPackets: [] },
    })).rejects.toThrow('Macro fallback cycle detected');
  });

  it('fails a macro when quality threshold is not met despite stage success', async () => {
    const qualityMacro: MacroDefinition = {
      name: 'quality-check',
      description: 'Enforces strict QA thresholds',
      qualityThreshold: 0.95,
      stages: [
        {
          id: 'qa-only',
          name: 'QA',
          description: 'Runs QA with reduced coverage',
          agentRole: AgentRole.QA,
          retryLimit: 0,
          continueOnError: false,
        },
      ],
    };
    const registry = new Map([[qualityMacro.name, qualityMacro]]);
    const orchestrator = new MacroOrchestrator(registry);
    const context = createContext();
    context.input = { technical: { lintErrors: 0, testFailures: 0, coverage: 0.7 } };
    const result = await orchestrator.runMacro('quality-check', context);
    expect(result.success).toBe(false);
  });
});
