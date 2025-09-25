import type { QAResult, QAIssue } from '../shared/types.js';
import { runAestheticChecks } from './aesthetic.js';
import { runNarrativeChecks } from './narrative.js';
import { runTechnicalChecks } from './technical.js';

interface QAInputs {
  aesthetic: Parameters<typeof runAestheticChecks>[0];
  narrative: Parameters<typeof runNarrativeChecks>[0];
  technical: Parameters<typeof runTechnicalChecks>[0];
}

export class QAEngine {
  runQA(inputs: QAInputs): QAResult {
    const issues: QAIssue[] = [];
    issues.push(...runAestheticChecks(inputs.aesthetic));
    issues.push(...runTechnicalChecks(inputs.technical));
    issues.push(...runNarrativeChecks(inputs.narrative));
    const hasError = issues.some((issue) => issue.severity === 'error');
    return { success: !hasError, issues };
  }
}
