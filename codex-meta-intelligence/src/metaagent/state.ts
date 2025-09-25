import { LruCache, generateId, nowIso } from '../shared/utils.js';
import type { MacroResult, MetaStateSnapshot, MetaTask } from '../shared/types.js';

export class MetaAgentState {
  private readonly queued: MetaTask[] = [];

  private readonly running: MetaTask[] = [];

  private readonly completed: MacroResult[] = [];

  private readonly metrics = new Map<string, number>();

  private readonly recentTasks = new LruCache<string, MetaTask>(100);

  enqueueTask(task: Omit<MetaTask, 'id' | 'requestedAt'>): MetaTask {
    const fullTask: MetaTask = {
      ...task,
      id: generateId('task'),
      requestedAt: nowIso(),
    };
    this.queued.push(fullTask);
    this.recentTasks.set(fullTask.id, fullTask);
    this.incrementMetric('tasks_enqueued');
    return fullTask;
  }

  startNextTask(): MetaTask | undefined {
    const task = this.queued.shift();
    if (!task) {
      return undefined;
    }
    this.running.push(task);
    this.incrementMetric('tasks_started');
    return task;
  }

  pullTask(taskId: string): MetaTask | undefined {
    const index = this.queued.findIndex((task) => task.id === taskId);
    if (index === -1) {
      return undefined;
    }
    const [task] = this.queued.splice(index, 1);
    if (!task) {
      return undefined;
    }
    this.running.push(task);
    this.incrementMetric('tasks_started');
    return task;
  }

  completeTask(taskId: string, result: MacroResult): void {
    const index = this.running.findIndex((task) => task.id === taskId);
    if (index !== -1) {
      this.running.splice(index, 1);
    }
    this.completed.push(result);
    this.incrementMetric(result.success ? 'tasks_succeeded' : 'tasks_failed');
  }

  cancelTask(taskId: string): boolean {
    const inQueue = this.removeTask(this.queued, taskId);
    const inRunning = this.removeTask(this.running, taskId);
    if (inQueue || inRunning) {
      this.incrementMetric('tasks_cancelled');
    }
    return inQueue || inRunning;
  }

  getSnapshot(): MetaStateSnapshot {
    return {
      queued: [...this.queued],
      running: [...this.running],
      completed: [...this.completed],
      metrics: Object.fromEntries(this.metrics.entries()),
    };
  }

  getTask(taskId: string): MetaTask | undefined {
    return (
      this.running.find((task) => task.id === taskId) ||
      this.queued.find((task) => task.id === taskId) ||
      this.recentTasks.get(taskId)
    );
  }

  private removeTask(tasks: MetaTask[], taskId: string): boolean {
    const index = tasks.findIndex((task) => task.id === taskId);
    if (index === -1) return false;
    tasks.splice(index, 1);
    return true;
  }

  private incrementMetric(name: string): void {
    const current = this.metrics.get(name) ?? 0;
    this.metrics.set(name, current + 1);
  }
}
