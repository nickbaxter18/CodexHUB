import { execSync } from 'node:child_process';

interface TestResult {
  command: string;
  success: boolean;
  output: string;
}

export const runTestCommand = (command: string): TestResult => {
  try {
    const output = execSync(command, { encoding: 'utf8', stdio: 'pipe' });
    return { command, success: true, output };
  } catch (error) {
    const err = error as Error & { stdout?: string; stderr?: string };
    return {
      command,
      success: false,
      output: `${err.stdout ?? ''}${err.stderr ?? err.message}`,
    };
  }
};
