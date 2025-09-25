import type { AgentGuidelines } from '../shared/types.js';

export interface ComplianceReport {
  executedCommands: string[];
  missingCommands: string[];
}

export const verifyCompliance = (
  guidelines: AgentGuidelines,
  executed: string[]
): ComplianceReport => {
  const missingCommands = guidelines.testing.filter((command) => !executed.includes(command));
  return {
    executedCommands: executed,
    missingCommands,
  };
};
