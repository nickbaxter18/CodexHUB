import { MacroOrchestrator } from '../macro/index.js';
import type { MacroContext, MetaStateSnapshot, MetaTask } from '../shared/types.js';
import { MetaAgentMonitor } from './monitor.js';
import { MetaAgentScheduler } from './scheduler.js';
import { MetaAgentState } from './state.js';

export class MetaAgent {
  private readonly state: MetaAgentState;

  private readonly scheduler: MetaAgentScheduler;

  private readonly monitor: MetaAgentMonitor;

  private readonly contexts = new Map<string, MacroContext>();

  private processing = false;

  constructor(
    state = new MetaAgentState(),
    scheduler = new MetaAgentScheduler(new MacroOrchestrator()),
    monitor = new MetaAgentMonitor()
  ) {
    this.state = state;
    this.scheduler = scheduler;
    this.monitor = monitor;
  }

  enqueueTask(task: Omit<MetaTask, 'id' | 'requestedAt'>, context: MacroContext): string {
    const stored = this.state.enqueueTask(task);
    this.contexts.set(stored.id, context);
    this.monitor.recordTaskQueued(stored);
    void this.processQueue();
    return stored.id;
  }

  cancelTask(taskId: string): boolean {
    const cancelled = this.state.cancelTask(taskId);
    if (cancelled) {
      this.contexts.delete(taskId);
    }
    return cancelled;
  }

  getState(): MetaStateSnapshot {
    return this.state.getSnapshot();
  }

  private async processQueue(): Promise<void> {
    if (this.processing) {
      return;
    }
    this.processing = true;
    try {
      while (true) {
        const snapshot = this.state.getSnapshot();
        const next = this.scheduler.chooseNextTask(snapshot.queued);
        if (!next) {
          break;
        }
        const task = this.state.pullTask(next.id);
        if (!task) {
          break;
        }
        const context = this.contexts.get(task.id);
        if (!context) {
          this.state.completeTask(task.id, {
            taskId: task.id,
            macroName: task.macroName,
            stageResults: [],
            success: false,
            startedAt: task.requestedAt,
            finishedAt: new Date().toISOString(),
          });
          continue;
        }
        this.monitor.recordTaskStarted(task);
        // eslint-disable-next-line no-await-in-loop
        const result = await this.scheduler.executeTask(task, context);
        this.state.completeTask(task.id, result);
        this.monitor.recordTaskCompleted(result);
        this.contexts.delete(task.id);
      }
    } finally {
      this.processing = false;
      this.monitor.recordHeartbeat();
    }
  }
}
