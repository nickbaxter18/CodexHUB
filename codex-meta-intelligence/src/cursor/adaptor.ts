import type { AgentGuidelines } from '../shared/types.js';
import merge from 'lodash.merge';

interface CursorRules {
  environment?: string[];
  testing?: string[];
  coding?: string[];
  logging?: string[];
  pullRequests?: string[];
}

export const mergeCursorRules = (
  guidelines: AgentGuidelines,
  cursorRules: CursorRules
): AgentGuidelines => {
  return merge({}, guidelines, cursorRules);
};
