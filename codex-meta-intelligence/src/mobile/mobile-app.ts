import { EventEmitter } from 'node:events';

import type { MobileGoal, MobileGoalInput } from '../shared/types.js';
import { generateId, nowIso } from '../shared/utils.js';

interface MobileAppEvents {
  created: [MobileGoal];
  updated: [MobileGoal];
}

class MobileControl extends EventEmitter<MobileAppEvents> {
  private readonly goals = new Map<string, MobileGoal>();

  private active = false;

  start(): void {
    if (this.active) {
      return;
    }
    this.active = true;
  }

  stop(): void {
    this.goals.clear();
    this.active = false;
  }

  isActive(): boolean {
    return this.active;
  }

  createGoal(input: MobileGoalInput): MobileGoal {
    if (!this.active) {
      throw new Error('Mobile control is not active');
    }
    const goal: MobileGoal = {
      id: generateId('goal'),
      title: input.title,
      description: input.description,
      priority: input.priority ?? 'medium',
      status: 'pending',
      createdAt: nowIso(),
      updatedAt: nowIso(),
    };
    this.goals.set(goal.id, goal);
    this.emit('created', goal);
    return goal;
  }

  listGoals(): MobileGoal[] {
    return Array.from(this.goals.values());
  }

  updateGoal(id: string, status: MobileGoal['status']): MobileGoal {
    const goal = this.goals.get(id);
    if (!goal) {
      throw new Error(`Goal ${id} not found`);
    }
    const updated: MobileGoal = {
      ...goal,
      status,
      updatedAt: nowIso(),
    };
    this.goals.set(id, updated);
    this.emit('updated', updated);
    return updated;
  }
}

let controller: MobileControl | undefined;

const ensureController = (): MobileControl => {
  if (!controller) {
    controller = new MobileControl();
  }
  return controller;
};

export const startMobileApp = async (): Promise<MobileControl> => {
  const instance = ensureController();
  instance.start();
  return instance;
};

export const stopMobileApp = (): void => {
  controller?.stop();
  controller = undefined;
};

export const isMobileControlActive = (): boolean => controller?.isActive() ?? false;

export const createGoal = async (input: MobileGoalInput): Promise<MobileGoal> => {
  const instance = ensureController();
  if (!instance.isActive()) {
    instance.start();
  }
  return instance.createGoal(input);
};

export const getGoals = async (): Promise<MobileGoal[]> => {
  const instance = ensureController();
  if (!instance.isActive()) {
    instance.start();
  }
  return instance.listGoals();
};

export const approveGoal = async (goalId: string): Promise<MobileGoal> => {
  const instance = ensureController();
  if (!instance.isActive()) {
    instance.start();
  }
  return instance.updateGoal(goalId, 'approved');
};

export const completeGoal = async (goalId: string): Promise<MobileGoal> => {
  const instance = ensureController();
  if (!instance.isActive()) {
    instance.start();
  }
  return instance.updateGoal(goalId, 'completed');
};

export type { MobileControl };
