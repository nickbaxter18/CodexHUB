import Ajv from 'ajv';

import type {
  AgentRole,
  AgentResult,
  ContextPacket,
  MacroContext,
  MacroDefinition,
  MacroResult,
  MacroStage,
} from '../shared/types.js';
import { deepFreeze } from '../shared/utils.js';

const ajv = new Ajv({ allErrors: true, removeAdditional: 'failing' });

const macroStageSchema = {
  type: 'object',
  required: ['id', 'name', 'description', 'agentRole', 'retryLimit', 'continueOnError'],
  additionalProperties: false,
  properties: {
    id: { type: 'string' },
    name: { type: 'string' },
    description: { type: 'string' },
    agentRole: { type: 'string' },
    retryLimit: { type: 'integer', minimum: 0 },
    continueOnError: { type: 'boolean' },
  },
};

const macroDefinitionSchema = {
  type: 'object',
  required: ['name', 'description', 'stages', 'qualityThreshold'],
  additionalProperties: false,
  properties: {
    name: { type: 'string' },
    description: { type: 'string' },
    stages: { type: 'array', items: macroStageSchema, minItems: 1 },
    fallbackMacro: { type: 'string' },
    qualityThreshold: { type: 'number', minimum: 0, maximum: 1 },
  },
};

const validate = <T>(schema: object, payload: unknown): T => {
  const compiled = ajv.compile<T>(schema);
  if (!compiled(payload)) {
    throw new Error(ajv.errorsText(compiled.errors, { dataVar: 'macro' }));
  }
  return payload as T;
};

export const validateMacroDefinition = (payload: unknown): MacroDefinition =>
  validate<MacroDefinition>(macroDefinitionSchema, payload);

export interface MacroExecutionContext {
  context: MacroContext;
  definition: MacroDefinition;
}

export interface MacroStageExecutionResult {
  stage: MacroStage;
  result: AgentResult;
  attempts: number;
  updatedContext: ContextPacket[];
}

export type MacroRegistry = Map<string, MacroDefinition>;

deepFreeze(macroStageSchema);
deepFreeze(macroDefinitionSchema);

export type { AgentRole, MacroContext, MacroDefinition, MacroResult, MacroStage };
