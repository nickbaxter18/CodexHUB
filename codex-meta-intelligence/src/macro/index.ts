import { createAgent } from '../agent/index.js';
import { AgentGuidelineReader } from '../agent/reader.js';
import { DEFAULT_AGENT_TIMEOUT_MS } from '../shared/constants.js';
import {
  AgentRole,
  type AgentResult,
  type ContextPacket,
  type MacroContext,
  type MacroDefinition,
  type MacroResult,
  type MacroStage,
} from '../shared/types.js';
import { generateId, nowIso } from '../shared/utils.js';
import { createDefaultMacroRegistry } from './scripts.js';
import {
  validateMacroDefinition,
  type MacroRegistry,
  type MacroStageExecutionResult,
} from './types.js';

const toContextPackets = (metadata: Record<string, unknown>): ContextPacket[] => {
  const value = metadata['contextPackets'];
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is ContextPacket => typeof item === 'object' && item !== null);
};

export class MacroOrchestrator {
  private readonly registry: MacroRegistry;

  private readonly guidelineReader: AgentGuidelineReader;

  constructor(registry: MacroRegistry = createDefaultMacroRegistry()) {
    this.registry = registry;
    this.guidelineReader = new AgentGuidelineReader();
    for (const definition of registry.values()) {
      validateMacroDefinition(definition);
    }
  }

  async runMacro(name: string, context: MacroContext): Promise<MacroResult> {
    const definition = this.registry.get(name);
    if (!definition) {
      throw new Error(`Macro '${name}' not found`);
    }

    const startedAt = nowIso();
    const stageResults: AgentResult[] = [];

    try {
      const packets = toContextPackets(context.metadata);
      for (const stage of definition.stages) {
        const execution = await this.executeStage(stage, definition, context, packets);
        stageResults.push(execution.result);
        if (execution.result.status === 'error' && !stage.continueOnError) {
          throw new Error(`Stage ${stage.name} failed: ${execution.result.summary}`);
        }
      }
      return {
        taskId: context.taskId,
        macroName: definition.name,
        stageResults,
        success: true,
        startedAt,
        finishedAt: nowIso(),
      };
    } catch (error) {
      if (definition.fallbackMacro) {
        return this.runMacro(definition.fallbackMacro, context);
      }
      const result: MacroResult = {
        taskId: context.taskId,
        macroName: definition.name,
        stageResults,
        success: false,
        startedAt,
        finishedAt: nowIso(),
      };
      return result;
    }
  }

  private async executeStage(
    stage: MacroStage,
    definition: MacroDefinition,
    context: MacroContext,
    packets: ContextPacket[]
  ): Promise<MacroStageExecutionResult> {
    const agent = createAgent(stage.agentRole as AgentRole, {
      id: `${stage.id}-${generateId('agent')}`,
      concurrency: 1,
      timeoutMs: DEFAULT_AGENT_TIMEOUT_MS,
      tools: [],
    });
    const guidelines = await this.guidelineReader.mergeGuidelines(process.cwd());
    let attempts = 0;
    let result: AgentResult | undefined;
    do {
      attempts += 1;
      const message = {
        taskId: context.taskId,
        macroId: definition.name,
        payload: context.input,
        context: packets,
        guidelines,
        metadata: {
          priority: 0,
          createdAt: nowIso(),
          source: 'macro-orchestrator',
          version: '1.0.0',
        },
      };
      // eslint-disable-next-line no-await-in-loop
      result = await agent.handleMessage(message);
      if (result.status === 'success') {
        break;
      }
    } while (attempts <= stage.retryLimit);

    if (!result) {
      throw new Error(`Stage ${stage.name} did not produce a result`);
    }

    return { stage, result, attempts };
  }
}

export const runMacro = async (macroName: string, context: MacroContext): Promise<MacroResult> => {
  const orchestrator = new MacroOrchestrator();
  return orchestrator.runMacro(macroName, context);
};
