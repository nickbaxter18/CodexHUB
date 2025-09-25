import readline from 'node:readline';

import type { MetaAgent } from '../metaagent/index.js';
import type { MacroContext, MetaTask } from '../shared/types.js';
import { OperatorHooks } from './hooks.js';

export class OperatorInterface {
  private readonly hooks: OperatorHooks;

  constructor(private readonly metaAgent: MetaAgent) {
    this.hooks = new OperatorHooks(metaAgent);
    this.hooks.on('notification', (message) => {
      process.stdout.write(`\n[Operator] ${message}\n`);
    });
  }

  registerCommandHandlers(): void {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    rl.setPrompt('meta-agent> ');
    rl.prompt();
    rl.on('line', (line) => {
      const [command, ...args] = line.trim().split(/\s+/);
      switch (command) {
        case 'enqueue':
          this.enqueueCommand(args);
          break;
        case 'cancel':
          this.cancelCommand(args);
          break;
        case 'exit':
          rl.close();
          break;
        default:
          process.stdout.write('Unknown command\n');
      }
      rl.prompt();
    });
  }

  private enqueueCommand(args: string[]): void {
    const [macroName] = args;
    if (!macroName) {
      process.stdout.write('Usage: enqueue <macroName>\n');
      return;
    }
    const task: Omit<MetaTask, 'id' | 'requestedAt'> = {
      macroName,
      input: {},
      priority: 1,
      owner: 'operator',
    };
    const context: MacroContext = {
      taskId: macroName,
      operatorId: 'operator',
      input: {},
      metadata: {},
      guidelines: {
        environment: [],
        testing: [],
        coding: [],
        logging: [],
        pullRequests: [],
      },
    };
    this.hooks.enqueueTask(task, context);
  }

  private cancelCommand(args: string[]): void {
    const [taskId] = args;
    if (!taskId) {
      process.stdout.write('Usage: cancel <taskId>\n');
      return;
    }
    this.hooks.cancelTask(taskId);
  }
}
