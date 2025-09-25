import { MacroOrchestrator } from '../macro/index.js';
import type { MacroContext, MetaStateSnapshot, MetaTask } from '../shared/types.js';
import { MetaAgentMonitor } from './monitor.js';
import { MetaAgentScheduler } from './scheduler.js';
import { MetaAgentState } from './state.js';
import { metricsRegistry, tracingService } from '../shared/runtime.js';

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
        const span = tracingService.startSpan('metaagent.processTask', {
          taskId: task.id,
          macro: task.macroName,
          priority: task.priority,
        });
        const startedAt = Date.now();
        // eslint-disable-next-line no-await-in-loop
        const result = await this.scheduler.executeTask(task, context);
        this.state.completeTask(task.id, result);
        this.monitor.recordTaskCompleted(result);
        tracingService.endSpan(span.id, {
          status: result.success ? 'success' : 'error',
          durationMs: Date.now() - startedAt,
        });
        metricsRegistry.record({
          name: 'metaagent_task_duration_ms',
          labels: { macro: task.macroName, success: String(result.success) },
          value: Date.now() - startedAt,
          timestamp: Date.now(),
        });
        metricsRegistry.record({
          name: 'metaagent_tasks_total',
          labels: { macro: task.macroName, outcome: result.success ? 'success' : 'error' },
          value: 1,
          timestamp: Date.now(),
        });
        this.contexts.delete(task.id);
      }
    } finally {
      this.processing = false;
      this.monitor.recordHeartbeat();
      const snapshot = this.state.getSnapshot();
      metricsRegistry.record({
        name: 'metaagent_queue_depth',
        labels: { state: 'queued' },
        value: snapshot.queued.length,
        timestamp: Date.now(),
      });
    }
  }
}
