import Ajv from 'ajv';
import {
  AgentRole,
  type AgentConfig,
  type AgentGuidelines,
  type AgentMessage,
  type AgentResult,
} from '../shared/types.js';
import { deepFreeze } from '../shared/utils.js';

const ajv = new Ajv({ allErrors: true, removeAdditional: 'failing', strict: false });

type Schema<T> = { validate: (value: unknown) => T };

const buildValidator = <T>(schema: object): Schema<T> => {
  const validate = ajv.compile<T>(schema);
  return {
    validate(value: unknown): T {
      if (!validate(value)) {
        const message = ajv.errorsText(validate.errors, { dataVar: 'payload' });
        throw new Error(`Validation failed: ${message}`);
      }
      return value as T;
    },
  };
};

export const agentConfigSchema = buildValidator<AgentConfig>({
  type: 'object',
  required: ['id', 'role', 'concurrency', 'timeoutMs', 'tools'],
  additionalProperties: false,
  properties: {
    id: { type: 'string', minLength: 1 },
    role: { enum: Object.values(AgentRole) },
    concurrency: { type: 'integer', minimum: 1 },
    timeoutMs: { type: 'integer', minimum: 1000 },
    tools: {
      type: 'array',
      items: { type: 'string' },
      default: [],
    },
  },
});

export const agentGuidelinesSchema = buildValidator<AgentGuidelines>({
  type: 'object',
  required: ['environment', 'testing', 'coding', 'logging', 'pullRequests'],
  properties: {
    environment: { type: 'array', items: { type: 'string' } },
    testing: { type: 'array', items: { type: 'string' } },
    coding: { type: 'array', items: { type: 'string' } },
    logging: { type: 'array', items: { type: 'string' } },
    pullRequests: { type: 'array', items: { type: 'string' } },
  },
  additionalProperties: false,
});

export const agentMessageSchema = buildValidator<AgentMessage>({
  type: 'object',
  required: ['taskId', 'macroId', 'payload', 'context', 'guidelines', 'metadata'],
  additionalProperties: false,
  properties: {
    taskId: { type: 'string', minLength: 1 },
    macroId: { type: 'string', minLength: 1 },
    payload: {},
    context: {
      type: 'array',
      items: { type: 'object' },
    },
    guidelines: agentGuidelinesSchema,
    metadata: {
      type: 'object',
      required: ['priority', 'createdAt', 'source', 'version'],
      additionalProperties: false,
      properties: {
        priority: { type: 'integer', minimum: 0 },
        createdAt: { type: 'string' },
        source: { type: 'string' },
        version: { type: 'string' },
      },
    },
  },
});

export const agentResultSchema = buildValidator<AgentResult>({
  type: 'object',
  required: ['taskId', 'status', 'summary', 'artifacts', 'issues', 'contextUpdates', 'durationMs'],
  additionalProperties: false,
  properties: {
    taskId: { type: 'string' },
    status: { enum: ['success', 'error'] },
    summary: { type: 'string' },
    artifacts: {
      type: 'object',
      additionalProperties: true,
    },
    issues: {
      type: 'array',
      items: { type: 'string' },
    },
    contextUpdates: {
      type: 'array',
      items: { type: 'object' },
    },
    durationMs: { type: 'integer', minimum: 0 },
    error: { type: 'string' },
  },
});

deepFreeze(agentConfigSchema);
deepFreeze(agentMessageSchema);
deepFreeze(agentResultSchema);

type Validator<T> = (value: unknown) => T;

export const validateAgentConfig: Validator<AgentConfig> = (value) =>
  agentConfigSchema.validate(value);
export const validateAgentMessage: Validator<AgentMessage> = (value) =>
  agentMessageSchema.validate(value);
export const validateAgentResult: Validator<AgentResult> = (value) =>
  agentResultSchema.validate(value);

export type { AgentConfig, AgentGuidelines, AgentMessage, AgentResult };
