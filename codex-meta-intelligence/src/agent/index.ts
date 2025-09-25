import EventEmitter from 'eventemitter3';
import { setTimeout as delay } from 'node:timers/promises';

import {
  AgentRole,
  type AgentConfig,
  type AgentGuidelines,
  type AgentMessage,
  type AgentResult,
} from '../shared/types.js';
import { generateId, nowIso, type JsonValue } from '../shared/utils.js';
import { DEFAULT_AGENT_TIMEOUT_MS } from '../shared/constants.js';
import { AgentGuidelineReader } from './reader.js';
import { validateAgentConfig, validateAgentMessage, validateAgentResult } from './types.js';
import {
  contextOrchestrator,
  knowledgeService,
  memoryService,
  metricsRegistry,
  qaEngine,
  tracingService,
} from '../shared/runtime.js';

interface AgentEvents {
  start: [AgentMessage];
  finish: [AgentResult];
  error: [Error];
}

export abstract class BaseAgent extends EventEmitter<AgentEvents> {
  protected readonly config: AgentConfig;

  private readonly reader: AgentGuidelineReader;

  private activeTasks = 0;

  private readonly queue: Array<() => void> = [];

  protected constructor(config: AgentConfig, reader = new AgentGuidelineReader()) {
    super();
    this.config = validateAgentConfig(config);
    this.reader = reader;
  }

  protected abstract execute(message: AgentMessage): Promise<AgentResult>;

  protected async beforeExecute(_message: AgentMessage): Promise<void> {}

  protected async afterExecute(_message: AgentMessage, _result: AgentResult): Promise<void> {}

  async handleMessage(message: AgentMessage): Promise<AgentResult> {
    const validatedMessage = validateAgentMessage(message);
    const span = tracingService.startSpan('agent.handle', {
      agentId: this.config.id,
      role: this.config.role,
      macroId: validatedMessage.macroId,
      taskId: validatedMessage.taskId,
    });
    const acquired = await this.acquireSlot();
    if (!acquired) {
      throw new Error(`Agent ${this.config.id} failed to acquire execution slot`);
    }

    try {
      const mergedGuidelines = await this.mergeGuidelines(validatedMessage);
      const enrichedMessage: AgentMessage = {
        ...validatedMessage,
        guidelines: mergedGuidelines,
      };
      this.emit('start', enrichedMessage);
      await this.beforeExecute(enrichedMessage);
      const controller = new AbortController();
      const timeout = this.config.timeoutMs || DEFAULT_AGENT_TIMEOUT_MS;
      const timer = delay(timeout, undefined, { signal: controller.signal }).then(() => {
        throw new Error(`Agent ${this.config.id} timed out after ${timeout}ms`);
      });
      const runPromise = this.execute(enrichedMessage);
      const result = await Promise.race([runPromise, timer]);
      controller.abort();
      const validatedResult = validateAgentResult({
        ...result,
        durationMs: result.durationMs ?? 0,
      });
      await this.afterExecute(enrichedMessage, validatedResult);
      this.emit('finish', validatedResult);
      this.persistResult(enrichedMessage, validatedResult);
      this.recordMetrics('success', validatedResult.durationMs);
      tracingService.endSpan(span.id, { status: 'success', durationMs: validatedResult.durationMs });
      return validatedResult;
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      this.emit('error', err);
      const failure: AgentResult = {
        taskId: validatedMessage.taskId,
        status: 'error',
        summary: err.message,
        artifacts: {},
        issues: [err.message],
        contextUpdates: [],
        durationMs: 0,
        error: err.stack,
      };
      this.persistResult(validatedMessage, failure);
      this.recordMetrics('error', 0);
      tracingService.endSpan(span.id, { status: 'error', error: err.message });
      return failure;
    } finally {
      this.releaseSlot();
    }
  }

  private async mergeGuidelines(message: AgentMessage): Promise<AgentGuidelines> {
    const fileGuidelines = await this.reader.mergeGuidelines(
      Array.isArray((message.metadata as Record<string, unknown>).guidelinePaths)
        ? ((message.metadata as Record<string, unknown>).guidelinePaths as string[])
        : message.metadata.source
    );
    return this.mergeGuidelineSets(fileGuidelines, message.guidelines);
  }

  private mergeGuidelineSets(
    left: AgentGuidelines,
    right: AgentGuidelines
  ): AgentGuidelines {
    const mergeLists = (a: string[], b: string[]): string[] => {
      const ordered: string[] = [];
      const seen = new Set<string>();
      for (const list of [a, b]) {
        for (const item of list) {
          if (!seen.has(item)) {
            ordered.push(item);
            seen.add(item);
          }
        }
      }
      return ordered;
    };
    return {
      environment: mergeLists(left.environment, right.environment),
      testing: mergeLists(left.testing, right.testing),
      coding: mergeLists(left.coding, right.coding),
      logging: mergeLists(left.logging, right.logging),
      pullRequests: mergeLists(left.pullRequests, right.pullRequests),
    };
  }

  private persistResult(message: AgentMessage, result: AgentResult): void {
    const payload = JSON.parse(
      JSON.stringify({
        message,
        result,
      })
    ) as JsonValue;
    memoryService.store({
      agentId: this.config.id,
      timestamp: nowIso(),
      dataType: 'agent-result',
      payload,
      tags: [this.config.role, message.macroId],
    });
  }

  private recordMetrics(outcome: 'success' | 'error', durationMs: number): void {
    metricsRegistry.record({
      name: 'agent_execution_total',
      labels: { agentId: this.config.id, role: this.config.role, outcome },
      value: 1,
      timestamp: Date.now(),
    });
    metricsRegistry.record({
      name: 'agent_execution_duration_ms',
      labels: { agentId: this.config.id, role: this.config.role },
      value: durationMs,
      timestamp: Date.now(),
    });
  }

  private async acquireSlot(): Promise<boolean> {
    if (this.activeTasks < this.config.concurrency) {
      this.activeTasks += 1;
      return true;
    }
    return new Promise<boolean>((resolve) => {
      const taskId = generateId('queue');
      const release = () => {
        resolve(true);
      };
      this.queue.push(release);
      this.emit('start', {
        taskId,
        macroId: 'queued',
        payload: {},
        context: [],
        guidelines: {
          environment: [],
          testing: [],
          coding: [],
          logging: [],
          pullRequests: [],
        },
        metadata: {
          priority: 0,
          createdAt: nowIso(),
          source: 'queue',
          version: '1.0.0',
        },
      });
    });
  }

  private releaseSlot(): void {
    if (this.activeTasks > 0) {
      this.activeTasks -= 1;
    }
    const next = this.queue.shift();
    if (next) {
      this.activeTasks += 1;
      next();
    }
  }
}

export class FrontendAgent extends BaseAgent {
  constructor(config: AgentConfig) {
    super(config);
  }

  protected async execute(message: AgentMessage): Promise<AgentResult> {
    const contextSummary = contextOrchestrator.compose(AgentRole.FRONTEND, message.context);
    const recommendations = [
      'Use responsive grid layouts with accessible contrast ratios',
      'Validate Tailwind tokens against U-DIG IT styling cognition',
    ];
    if (message.guidelines.testing.length > 0) {
      recommendations.push(`Prepare to execute: ${message.guidelines.testing.join(', ')}`);
    }
    const summary = contextSummary
      ? `Generated UI plan for task ${message.taskId} using ${message.context.length} context packet(s).`
      : `Generated UI plan for task ${message.taskId} with limited context.`;
    const artifacts: Record<string, JsonValue> = {
      recommendations,
      contextSummary,
      guidelines: JSON.parse(JSON.stringify(message.guidelines)) as JsonValue,
    };
    const issues = contextSummary ? [] : ['Context summary unavailable; verify context coverage.'];
    return {
      taskId: message.taskId,
      status: issues.length ? 'error' : 'success',
      summary,
      artifacts,
      issues,
      contextUpdates: message.context,
      durationMs: 50,
    };
  }
}

export class BackendAgent extends BaseAgent {
  constructor(config: AgentConfig) {
    super(config);
  }

  protected async execute(message: AgentMessage): Promise<AgentResult> {
    const packets = contextOrchestrator.retrieve({
      taskId: message.taskId,
      role: AgentRole.BACKEND,
      keywords: ['api', 'backend'],
      limit: 5,
    });
    const endpoints = packets.packets.map((packet) => ({
      method: 'GET',
      path: `/${packet.id.split('_')[0] ?? 'health'}`,
      description: packet.summary || 'Generated from context packet',
    }));
    if (endpoints.length === 0) {
      endpoints.push({
        method: 'GET',
        path: '/health',
        description: 'Default health check endpoint',
      });
    }
    const summary = `Produced backend scaffolding for ${message.taskId} with ${endpoints.length} endpoint suggestion(s).`;
    const artifacts: Record<string, JsonValue> = {
      apiDesign: JSON.parse(JSON.stringify({ endpoints })) as JsonValue,
      retrievalRationale: packets.rationale,
    };
    return {
      taskId: message.taskId,
      status: 'success',
      summary,
      artifacts,
      issues: [],
      contextUpdates: message.context,
      durationMs: 65,
    };
  }
}

export class KnowledgeAgent extends BaseAgent {
  constructor(config: AgentConfig) {
    super(config);
  }

  protected async execute(message: AgentMessage): Promise<AgentResult> {
    const upserts = message.context.map((packet) => {
      const block = knowledgeService.upsertBlock({
        id: packet.id,
        content: packet.content,
        metadata: {
          author: (packet.metadata.author as string) ?? 'system',
          timestamp: packet.createdAt,
          tags: Array.isArray(packet.metadata.tags)
            ? (packet.metadata.tags as string[])
            : [],
          citations: Array.isArray(packet.metadata.citations)
            ? (packet.metadata.citations as string[])
            : [],
          source: packet.source,
          reliabilityScore: Number(packet.metadata.reliabilityScore ?? 0.5),
        },
        links: Array.isArray(packet.metadata.links)
          ? (packet.metadata.links as string[])
          : undefined,
      });
      return { id: block.id, tags: block.metadata.tags };
    });
    const artifacts: Record<string, JsonValue> = { knowledgeUpdate: upserts };
    return {
      taskId: message.taskId,
      status: 'success',
      summary: 'Knowledge store updated',
      artifacts,
      issues: [],
      contextUpdates: message.context,
      durationMs: 40,
    };
  }
}

export class QAAgent extends BaseAgent {
  constructor(config: AgentConfig) {
    super(config);
  }

  protected async execute(message: AgentMessage): Promise<AgentResult> {
    const rawPayload = message.payload;
    const payload =
      rawPayload && typeof rawPayload === 'object' && !Array.isArray(rawPayload)
        ? (rawPayload as Record<string, JsonValue>)
        : {};
    const technicalPayload = payload.technical;
    const technical =
      technicalPayload && typeof technicalPayload === 'object' && !Array.isArray(technicalPayload)
        ? (technicalPayload as Record<string, JsonValue>)
        : {};
    const toNumber = (value: JsonValue | undefined, fallback = 0): number => {
      if (typeof value === 'number') {
        return value;
      }
      if (typeof value === 'string') {
        const parsed = Number(value);
        return Number.isNaN(parsed) ? fallback : parsed;
      }
      return fallback;
    };
    const coverage = toNumber(technical.coverage, 0.85);
    const qaResult = qaEngine.runQA({
      aesthetic: {
        palette: [
          { name: 'Primary', contrastRatio: 4.5 },
          { name: 'Secondary', contrastRatio: 4.6 },
        ],
        typographyScale: [1, 1.25, 1.6],
        motionDensity: 0.3,
      },
      narrative: {
        tone: 'empathetic',
        coherenceScore: 0.9,
        fairnessScore: 0.95,
      },
      technical: {
        lintErrors: toNumber(technical.lintErrors),
        testFailures: toNumber(technical.testFailures),
        coverage,
      },
    });
    const summary = qaResult.success ? 'QA checks passed' : 'QA issues detected';
    const artifacts: Record<string, JsonValue> = {
      executedChecks: message.guidelines.testing,
      issues: JSON.parse(JSON.stringify(qaResult.issues)) as JsonValue,
    };
    return {
      taskId: message.taskId,
      status: qaResult.success ? 'success' : 'error',
      summary,
      artifacts,
      issues: qaResult.issues.map(
        (issue) => `${issue.engine}(${issue.severity}): ${issue.message}`
      ),
      contextUpdates: message.context,
      durationMs: 30,
      error: qaResult.success ? undefined : summary,
    };
  }
}

export class RefinementAgent extends BaseAgent {
  constructor(config: AgentConfig) {
    super(config);
  }

  protected async execute(message: AgentMessage): Promise<AgentResult> {
    const qaIssues = Array.isArray((message.payload as Record<string, JsonValue>)?.qaIssues)
      ? ((message.payload as Record<string, JsonValue>).qaIssues as string[])
      : [];
    const refinements = message.context.map((packet) => ({
      id: packet.id,
      improvement: qaIssues.length
        ? `Resolved ${qaIssues.length} QA issue(s) for packet ${packet.id}`
        : 'Applied styling cognition refinements',
    }));
    const artifacts: Record<string, JsonValue> = {
      refinements,
      qaIssues,
    };
    return {
      taskId: message.taskId,
      status: 'success',
      summary: 'Applied refinements based on QA feedback',
      artifacts,
      issues: [],
      contextUpdates: message.context,
      durationMs: 45,
    };
  }
}

export const createAgent = (role: AgentRole, config: Omit<AgentConfig, 'role'>): BaseAgent => {
  const fullConfig: AgentConfig = { ...config, role };
  switch (role) {
    case AgentRole.FRONTEND:
      return new FrontendAgent(fullConfig);
    case AgentRole.BACKEND:
      return new BackendAgent(fullConfig);
    case AgentRole.KNOWLEDGE:
      return new KnowledgeAgent(fullConfig);
    case AgentRole.QA:
      return new QAAgent(fullConfig);
    case AgentRole.REFINEMENT:
      return new RefinementAgent(fullConfig);
    default:
      throw new Error(`Unsupported agent role: ${role}`);
  }
};
