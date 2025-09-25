import EventEmitter from 'eventemitter3';
import { setTimeout as delay } from 'node:timers/promises';

import {
  AgentRole,
  type AgentConfig,
  type AgentMessage,
  type AgentResult,
} from '../shared/types.js';
import { generateId, nowIso, type JsonValue } from '../shared/utils.js';
import { DEFAULT_AGENT_TIMEOUT_MS } from '../shared/constants.js';
import { AgentGuidelineReader } from './reader.js';
import { validateAgentConfig, validateAgentMessage, validateAgentResult } from './types.js';

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
    const acquired = await this.acquireSlot();
    if (!acquired) {
      throw new Error(`Agent ${this.config.id} failed to acquire execution slot`);
    }

    try {
      const mergedGuidelines = await this.reader.mergeGuidelines(validatedMessage.metadata.source);
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
      return failure;
    } finally {
      this.releaseSlot();
    }
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
    const summary = `Generated UI plan for task ${message.taskId}`;
    const artifacts: Record<string, JsonValue> = {
      recommendations: [
        'Use responsive grid layout with accessible contrast ratios',
        'Apply motion grammar micro-interactions for state changes',
      ],
      guidelines: JSON.parse(JSON.stringify(message.guidelines)) as JsonValue,
    };
    return {
      taskId: message.taskId,
      status: 'success',
      summary,
      artifacts,
      issues: [],
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
    const summary = `Produced backend scaffolding for ${message.taskId}`;
    const artifacts: Record<string, JsonValue> = {
      apiDesign: JSON.parse(
        JSON.stringify({
          endpoints: [
            {
              method: 'GET',
              path: '/health',
              description: 'Health check endpoint generated by BackendAgent',
            },
          ],
        })
      ) as JsonValue,
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
    const artifacts: Record<string, JsonValue> = {
      knowledgeUpdate: message.context.map((packet) => ({
        packetId: packet.id,
        summary: packet.summary,
      })),
    };
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
    const issues = message.context.length === 0 ? ['No context provided for QA'] : [];
    return {
      taskId: message.taskId,
      status: issues.length ? 'error' : 'success',
      summary: issues.length ? 'QA issues detected' : 'QA checks passed',
      artifacts: { executedChecks: message.guidelines.testing },
      issues,
      contextUpdates: message.context,
      durationMs: 30,
      error: issues.length ? 'Context missing' : undefined,
    };
  }
}

export class RefinementAgent extends BaseAgent {
  constructor(config: AgentConfig) {
    super(config);
  }

  protected async execute(message: AgentMessage): Promise<AgentResult> {
    const artifacts: Record<string, JsonValue> = {
      refinements: message.context.map((packet) => ({
        id: packet.id,
        improvement: 'Applied styling cognition refinements',
      })),
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
