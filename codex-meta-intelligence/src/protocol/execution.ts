import { PIPELINE_STAGES } from '../shared/constants.js';
import type { AgentResult } from '../shared/types.js';

export type ExecutionStageName = (typeof PIPELINE_STAGES)[number];

export interface ExecutionStage {
  name: ExecutionStageName;
  action: () => Promise<AgentResult>;
}

export interface ExecutionSummary {
  stages: Array<{ name: ExecutionStageName; result: AgentResult }>;
  success: boolean;
}

export class ExecutionPipeline {
  async runStage(stage: ExecutionStage): Promise<AgentResult> {
    return stage.action();
  }

  async run(stages: ExecutionStage[]): Promise<ExecutionSummary> {
    const results: Array<{ name: ExecutionStageName; result: AgentResult }> = [];
    for (const stage of stages) {
      // eslint-disable-next-line no-await-in-loop
      const result = await this.runStage(stage);
      results.push({ name: stage.name, result });
      if (result.status === 'error') {
        return { stages: results, success: false };
      }
    }
    return { stages: results, success: true };
  }
}

export const runPipeline = async (stages: ExecutionStage[]): Promise<ExecutionSummary> => {
  const pipeline = new ExecutionPipeline();
  return pipeline.run(stages);
};
