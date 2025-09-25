import { runLintCommand } from './linters.js';
import { runTestCommand } from './tests.js';

interface PipelineOptions {
  lintCommand?: string;
  testCommand?: string;
}

export interface PipelineOutcome {
  lint?: ReturnType<typeof runLintCommand>;
  tests?: ReturnType<typeof runTestCommand>;
}

export const runPipeline = (options: PipelineOptions = {}): PipelineOutcome => {
  const outcome: PipelineOutcome = {};
  if (options.lintCommand) {
    outcome.lint = runLintCommand(options.lintCommand);
  }
  if (options.testCommand) {
    outcome.tests = runTestCommand(options.testCommand);
  }
  return outcome;
};
