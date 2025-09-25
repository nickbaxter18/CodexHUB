import type { QAIssue } from '../shared/types.js';
import { validateStyling, type StylingDocument } from '../protocol/styling.js';

export const runAestheticChecks = (document: StylingDocument): QAIssue[] => {
  return validateStyling(document).map((issue) => ({
    engine: 'aesthetic',
    severity: issue.severity,
    message: `${issue.rule}: ${issue.message}`,
  }));
};
