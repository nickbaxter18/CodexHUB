import type { RiskAssessment } from '../shared/types.js';

interface RiskSignals {
  recentFailures: number;
  qaIssues: number;
  complexity: number;
}

export const assessRisk = (taskId: string, signals: RiskSignals): RiskAssessment => {
  const score = signals.recentFailures * 0.4 + signals.qaIssues * 0.4 + signals.complexity * 0.2;
  let level: RiskAssessment['level'] = 'low';
  if (score > 6) level = 'high';
  else if (score > 3) level = 'medium';
  return {
    taskId,
    riskScore: score,
    level,
    factors: [
      `Recent failures: ${signals.recentFailures}`,
      `QA issues: ${signals.qaIssues}`,
      `Complexity: ${signals.complexity}`,
    ],
  };
};
