import type { QAIssue } from '../shared/types.js';

interface TechnicalReport {
  lintErrors: number;
  testFailures: number;
  coverage: number;
}

export const runTechnicalChecks = (report: TechnicalReport): QAIssue[] => {
  const issues: QAIssue[] = [];
  if (report.lintErrors > 0) {
    issues.push({
      engine: 'technical',
      severity: 'error',
      message: `${report.lintErrors} lint errors detected`,
    });
  }
  if (report.testFailures > 0) {
    issues.push({
      engine: 'technical',
      severity: 'error',
      message: `${report.testFailures} test failures detected`,
    });
  }
  if (report.coverage < 0.8) {
    issues.push({
      engine: 'technical',
      severity: 'warning',
      message: `Test coverage below threshold: ${(report.coverage * 100).toFixed(1)}%`,
    });
  }
  return issues;
};
