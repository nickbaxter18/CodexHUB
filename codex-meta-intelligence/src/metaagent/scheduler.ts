import type { MacroContext, MetaTask } from '../shared/types.js';
import { nowIso } from '../shared/utils.js';
import { MacroOrchestrator } from '../macro/index.js';
import type { MacroResult } from '../shared/types.js';

export interface SchedulerStrategy {
  selectTask(queue: MetaTask[]): MetaTask | undefined;
}

export class PriorityScheduler implements SchedulerStrategy {
  selectTask(queue: MetaTask[]): MetaTask | undefined {
    if (queue.length === 0) return undefined;
    let highest: MetaTask | undefined;
    for (const task of queue) {
      if (!highest || task.priority > highest.priority) {
        highest = task;
      }
    }
    return highest;
  }
}

export class MetaAgentScheduler {
  private readonly orchestrator: MacroOrchestrator;

  private readonly strategy: SchedulerStrategy;

  constructor(
    orchestrator = new MacroOrchestrator(),
    strategy: SchedulerStrategy = new PriorityScheduler()
  ) {
    this.orchestrator = orchestrator;
    this.strategy = strategy;
  }

  async executeTask(task: MetaTask, context: MacroContext): Promise<MacroResult> {
    const enrichedContext: MacroContext = {
      ...context,
      metadata: {
        ...context.metadata,
        scheduledAt: nowIso(),
        priority: task.priority,
      },
    };
    return this.orchestrator.runMacro(task.macroName, enrichedContext);
  }

  chooseNextTask(queue: MetaTask[]): MetaTask | undefined {
    return this.strategy.selectTask(queue);
  }
}
