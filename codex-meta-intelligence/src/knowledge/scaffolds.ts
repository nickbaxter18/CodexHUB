import Ajv from 'ajv';

import type { KnowledgeBlock } from '../shared/types.js';

const ajv = new Ajv({ allErrors: true, strict: false });

const blockSchema = {
  type: 'object',
  required: ['id', 'content', 'metadata'],
  additionalProperties: false,
  properties: {
    id: { type: 'string' },
    content: { type: 'string' },
    metadata: {
      type: 'object',
      required: ['author', 'timestamp', 'tags', 'citations', 'source', 'reliabilityScore'],
      additionalProperties: false,
      properties: {
        author: { type: 'string' },
        timestamp: { type: 'string' },
        tags: { type: 'array', items: { type: 'string' } },
        citations: { type: 'array', items: { type: 'string' } },
        source: { type: 'string' },
        reliabilityScore: { type: 'number', minimum: 0, maximum: 1 },
      },
    },
    links: {
      type: 'array',
      items: { type: 'string' },
      default: [],
    },
  },
};

const validateBlock = ajv.compile<KnowledgeBlock>(blockSchema);

export const parseNdjson = (content: string): KnowledgeBlock[] => {
  const lines = content
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);
  return lines.map((line, index) => {
    const parsed = JSON.parse(line);
    if (!validateBlock(parsed)) {
      throw new Error(
        `Invalid knowledge block at line ${index + 1}: ${ajv.errorsText(validateBlock.errors)}`
      );
    }
    return parsed;
  });
};

export const validateKnowledgeBlock = (block: KnowledgeBlock): KnowledgeBlock => {
  if (!validateBlock(block)) {
    throw new Error(ajv.errorsText(validateBlock.errors));
  }
  return block;
};
