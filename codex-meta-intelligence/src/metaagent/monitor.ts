import EventEmitter from 'eventemitter3';

import type { MacroResult, MetaTask } from '../shared/types.js';
import type { MetricRecord } from '../shared/types.js';
import { nowIso } from '../shared/utils.js';

interface MonitorEvents {
  taskQueued: [MetaTask];
  taskStarted: [MetaTask];
  taskCompleted: [MacroResult];
  metric: [MetricRecord];
}

export class MetaAgentMonitor extends EventEmitter<MonitorEvents> {
  recordTaskQueued(task: MetaTask): void {
    this.emit('taskQueued', task);
    this.emit('metric', {
      name: 'metaagent.tasks.queued',
      labels: { macro: task.macroName },
      value: task.priority,
      timestamp: Date.now(),
    });
  }

  recordTaskStarted(task: MetaTask): void {
    this.emit('taskStarted', task);
    this.emit('metric', {
      name: 'metaagent.tasks.started',
      labels: { macro: task.macroName },
      value: 1,
      timestamp: Date.now(),
    });
  }

  recordTaskCompleted(result: MacroResult): void {
    this.emit('taskCompleted', result);
    this.emit('metric', {
      name: 'metaagent.tasks.completed',
      labels: { macro: result.macroName, success: String(result.success) },
      value: result.success ? 1 : 0,
      timestamp: Date.now(),
    });
  }

  recordHeartbeat(): void {
    this.emit('metric', {
      name: 'metaagent.heartbeat',
      labels: { timestamp: nowIso() },
      value: 1,
      timestamp: Date.now(),
    });
  }
}
