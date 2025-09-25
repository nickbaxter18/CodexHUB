import { movingAverage, weightedScore } from './analytics.js';
import { assessRisk as calculateRisk } from './risk.js';
import type { ForecastResult, RiskAssessment } from '../shared/types.js';

interface ForecastInputs {
  taskId: string;
  durations: number[];
  qaIssues: number[];
  weights?: number[];
}

export class ForesightEngine {
  predict(inputs: ForecastInputs): ForecastResult {
    const duration = movingAverage(inputs.durations, 5);
    const qaPenalty = weightedScore(
      inputs.qaIssues,
      inputs.weights ?? inputs.qaIssues.map(() => 1)
    );
    const predictedDurationMs = duration * (1 + qaPenalty * 0.1);
    const confidence = Math.max(0.4, 1 - qaPenalty * 0.05);
    return {
      taskId: inputs.taskId,
      predictedDurationMs,
      confidence,
      notes: [
        `Base duration estimate: ${duration.toFixed(2)}ms`,
        `QA penalty: ${qaPenalty.toFixed(2)}`,
      ],
    };
  }

  assessRisk(
    taskId: string,
    recentFailures: number,
    qaIssues: number,
    complexity: number
  ): RiskAssessment {
    return calculateRisk(taskId, { recentFailures, qaIssues, complexity });
  }
}
