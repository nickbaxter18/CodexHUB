import { createAgent } from '../agent/index.js';
import { AgentGuidelineReader } from '../agent/reader.js';
import { DEFAULT_AGENT_TIMEOUT_MS, QA_SEVERITY_ORDER } from '../shared/constants.js';
import {
  ExecutionPipeline,
  type ExecutionStage,
  type ExecutionStageName,
} from '../protocol/execution.js';
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

const inferStageName = (stage: MacroStage): ExecutionStageName => {
  switch (stage.agentRole) {
    case AgentRole.QA:
      return 'audit';
    case AgentRole.REFINEMENT:
      return 'refinement';
    default:
      return 'draft';
  }
};

export class MacroOrchestrator {
  private readonly registry: MacroRegistry;

  private readonly guidelineReader: AgentGuidelineReader;

  private readonly pipeline = new ExecutionPipeline();

  constructor(registry: MacroRegistry = createDefaultMacroRegistry()) {
    this.registry = registry;
    this.guidelineReader = new AgentGuidelineReader();
    for (const definition of registry.values()) {
      validateMacroDefinition(definition);
    }
  }

  async runMacro(name: string, context: MacroContext): Promise<MacroResult> {
    return this.runMacroInternal(name, context, new Set());
  }

  private async runMacroInternal(
    name: string,
    context: MacroContext,
    visited: Set<string>
  ): Promise<MacroResult> {
    const definition = this.registry.get(name);
    if (!definition) {
      throw new Error(`Macro '${name}' not found`);
    }
    if (visited.has(name)) {
      throw new Error(`Macro fallback cycle detected for '${name}'`);
    }
    visited.add(name);

    const startedAt = nowIso();
    const stageResults: AgentResult[] = [];
    const packets = toContextPackets(context.metadata);
    let workingContext = [...packets];

    const executionStages = definition.stages.map((stage): ExecutionStage => ({
      name: inferStageName(stage),
      allowFailure: stage.continueOnError,
      onResult: (result) => {
        stageResults.push(result);
        workingContext = result.contextUpdates.length > 0 ? result.contextUpdates : workingContext;
      },
      action: async () => {
        const execution = await this.executeStage(stage, definition, context, workingContext);
        workingContext = execution.updatedContext;
        return execution.result;
      },
    }));

    const pipelineResult = await this.pipeline.run(executionStages);
    const qualityScore = this.calculateQualityScore(stageResults);
    const meetsQuality = qualityScore >= definition.qualityThreshold;
    const success = pipelineResult.success && meetsQuality;

    if (!success && definition.fallbackMacro) {
      return this.runMacroInternal(definition.fallbackMacro, context, visited);
    }

    return {
      taskId: context.taskId,
      macroName: definition.name,
      stageResults,
      success,
      startedAt,
      finishedAt: nowIso(),
    };
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
    const guidelinePaths =
      (Array.isArray(context.metadata.guidelinePaths)
        ? (context.metadata.guidelinePaths as string[])
        : undefined) ?? [process.cwd()];
    const guidelines = await this.guidelineReader.mergeGuidelines(guidelinePaths);
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
          guidelinePaths,
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

    const updatedContext = result.contextUpdates.length > 0 ? result.contextUpdates : packets;
    return { stage, result, attempts, updatedContext };
  }

  private calculateQualityScore(results: AgentResult[]): number {
    if (results.length === 0) {
      return 0;
    }
    const successCount = results.filter((result) => result.status === 'success').length;
    const issuePenalty = results.reduce((total, result) => {
      return (
        total +
        result.issues.reduce((acc, issue) => {
          const severity = issue.includes('error') ? 'error' : issue.includes('warning') ? 'warning' : 'info';
          return acc + QA_SEVERITY_ORDER[severity as keyof typeof QA_SEVERITY_ORDER] * 0.1;
        }, 0)
      );
    }, 0);
    const baseScore = successCount / results.length;
    return Math.max(0, baseScore - issuePenalty);
  }
}

export const runMacro = async (macroName: string, context: MacroContext): Promise<MacroResult> => {
  const orchestrator = new MacroOrchestrator();
  return orchestrator.runMacro(macroName, context);
};
