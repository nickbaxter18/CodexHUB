import EventEmitter from 'eventemitter3';

import type { MetaAgent } from '../metaagent/index.js';
import type { MacroContext, MetaTask } from '../shared/types.js';

interface OperatorEvents {
  notification: [string];
}

export class OperatorHooks extends EventEmitter<OperatorEvents> {
  constructor(private readonly metaAgent: MetaAgent) {
    super();
  }

  enqueueTask(task: Omit<MetaTask, 'id' | 'requestedAt'>, context: MacroContext): string {
    const id = this.metaAgent.enqueueTask(task, context);
    this.emit('notification', `Task ${id} enqueued`);
    return id;
  }

  cancelTask(taskId: string): boolean {
    const cancelled = this.metaAgent.cancelTask(taskId);
    const message = cancelled ? `Task ${taskId} cancelled` : `Task ${taskId} not found`;
    this.emit('notification', message);
    return cancelled;
  }
}
