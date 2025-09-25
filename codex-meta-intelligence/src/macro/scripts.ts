import { AgentRole, type MacroDefinition } from '../shared/types.js';
import type { MacroRegistry } from './types.js';

const defaultMacros: MacroDefinition[] = [
  {
    name: 'full-pipeline',
    description: 'Runs draft, audit and refinement stages to produce deployable artifacts.',
    qualityThreshold: 0.8,
    stages: [
      {
        id: 'draft-ui',
        name: 'Draft UI',
        description: 'Generate initial frontend concept.',
        agentRole: AgentRole.FRONTEND,
        retryLimit: 1,
        continueOnError: false,
      },
      {
        id: 'draft-api',
        name: 'Draft API',
        description: 'Craft backend scaffold with health endpoint.',
        agentRole: AgentRole.BACKEND,
        retryLimit: 1,
        continueOnError: true,
      },
      {
        id: 'qa',
        name: 'Quality Assurance',
        description: 'Run QA checks to validate the draft.',
        agentRole: AgentRole.QA,
        retryLimit: 0,
        continueOnError: false,
      },
      {
        id: 'refine',
        name: 'Refinement',
        description: 'Apply improvements from QA findings.',
        agentRole: AgentRole.REFINEMENT,
        retryLimit: 1,
        continueOnError: true,
      },
    ],
  },
  {
    name: 'knowledge-refresh',
    description: 'Synchronise knowledge blocks and refresh context.',
    qualityThreshold: 0.6,
    stages: [
      {
        id: 'knowledge-update',
        name: 'Knowledge Update',
        description: 'Push context packets into the knowledge store.',
        agentRole: AgentRole.KNOWLEDGE,
        retryLimit: 2,
        continueOnError: false,
      },
      {
        id: 'qa-audit',
        name: 'QA Audit',
        description: 'Validate knowledge quality.',
        agentRole: AgentRole.QA,
        retryLimit: 1,
        continueOnError: false,
      },
    ],
    fallbackMacro: 'full-pipeline',
  },
];

export const createDefaultMacroRegistry = (): MacroRegistry => {
  const registry: MacroRegistry = new Map();
  for (const macro of defaultMacros) {
    registry.set(macro.name, macro);
  }
  return registry;
};

export const listMacros = (): MacroDefinition[] => [...defaultMacros];
