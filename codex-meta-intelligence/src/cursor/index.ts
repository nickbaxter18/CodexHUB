import { EventEmitter } from 'node:events';
import { watch, type FSWatcher } from 'node:fs';
import { readdir, stat } from 'node:fs/promises';
import path from 'node:path';

import type {
  CursorAgentType,
  CursorComplianceCheck,
  CursorComplianceReport,
} from '../shared/types.js';
import { DEFAULT_CURSOR_MONITOR_INTERVAL_MS } from '../shared/constants.js';
import {
  getKnowledgeEntries,
  isKnowledgeAutoLoaderActive,
  startKnowledgeAutoLoading,
} from '../knowledge/auto-loader.js';
import {
  getSections,
  getTags,
  isBrainBlocksActive,
  startBrainBlocksIntegration,
} from '../knowledge/brain-blocks-integration.js';
import { getGoals, isMobileControlActive, startMobileApp } from '../mobile/mobile-app.js';
import { clamp } from '../shared/utils.js';

interface CursorInvocationEvent {
  filePath: string;
  timestamp: number;
}

interface CursorAutoInvokerEvents {
  invocation: [CursorInvocationEvent];
  error: [Error];
}

const normalisePath = (target: string): string => path.resolve(target);

const globToRegExp = (pattern: string): RegExp => {
  const escaped = pattern
    .replace(/[.+^${}()|[\]\\]/g, '\\$&')
    .replace(/\*\*/g, '::DOUBLE_STAR::')
    .replace(/\*/g, '[^/]*')
    .replace(/::DOUBLE_STAR::/g, '.*');
  return new RegExp(`^${escaped}$`);
};

const parsePatterns = (raw: string | undefined): RegExp[] => {
  if (!raw) {
    return [globToRegExp('**/*.ts')];
  }
  return raw
    .split(',')
    .map((entry) => entry.trim())
    .filter(Boolean)
    .map((pattern) => globToRegExp(pattern));
};

const patterns = parsePatterns(process.env.CURSOR_FILE_PATTERNS);

class CursorAutoInvoker extends EventEmitter<CursorAutoInvokerEvents> {
  private readonly watchers = new Map<string, FSWatcher>();

  private readonly triggeredFiles = new Map<string, number>();

  private running = false;

  constructor(private readonly monitorIntervalMs: number) {
    super();
  }

  async start(paths: Iterable<string>): Promise<void> {
    if (this.running) {
      return;
    }
    for (const pathEntry of paths) {
      // eslint-disable-next-line no-await-in-loop
      await this.watchPath(normalisePath(pathEntry));
    }
    this.running = true;
  }

  stop(): void {
    for (const watcher of this.watchers.values()) {
      watcher.close();
    }
    this.watchers.clear();
    this.running = false;
    this.triggeredFiles.clear();
  }

  isRunning(): boolean {
    return this.running;
  }

  getWatchedPaths(): string[] {
    return Array.from(this.watchers.keys());
  }

  getTriggeredFiles(): string[] {
    return Array.from(this.triggeredFiles.keys());
  }

  getLastInvocation(): number | undefined {
    const timestamps = Array.from(this.triggeredFiles.values());
    return timestamps.length > 0 ? Math.max(...timestamps) : undefined;
  }

  private async watchPath(target: string): Promise<void> {
    try {
      const stats = await stat(target);
      if (stats.isDirectory()) {
        this.registerWatcher(target);
        const entries = await readdir(target, { withFileTypes: true });
        for (const entry of entries) {
          const entryPath = path.join(target, entry.name);
          if (entry.isDirectory()) {
            // eslint-disable-next-line no-await-in-loop
            await this.watchPath(entryPath);
          }
        }
      } else {
        const parent = path.dirname(target);
        this.registerWatcher(parent);
      }
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      this.emit('error', err);
    }
  }

  private registerWatcher(directory: string): void {
    if (this.watchers.has(directory)) {
      return;
    }
    const watcher = watch(directory, { persistent: false }, (eventType, fileName) => {
      if (!fileName) {
        return;
      }
      const absolutePath = normalisePath(path.join(directory, fileName.toString()));
      if (eventType === 'rename') {
        // Ensure new directories are watched.
        stat(absolutePath)
          .then((stats) => {
            if (stats.isDirectory()) {
              return this.watchPath(absolutePath);
            }
            return undefined;
          })
          .catch(() => undefined);
      }
      if (this.matchesPatterns(absolutePath)) {
        const now = Date.now();
        const last = this.triggeredFiles.get(absolutePath);
        if (!last || now - last >= this.monitorIntervalMs) {
          this.triggeredFiles.set(absolutePath, now);
          this.emit('invocation', { filePath: absolutePath, timestamp: now });
        }
      }
    });
    watcher.on('error', (error) => {
      const err = error instanceof Error ? error : new Error(String(error));
      this.emit('error', err);
    });
    this.watchers.set(directory, watcher);
  }

  private matchesPatterns(filePath: string): boolean {
    const relative = path.relative(process.cwd(), filePath);
    return patterns.some((pattern) => pattern.test(relative));
  }
}

let autoInvoker: CursorAutoInvoker | undefined;

const getMonitorInterval = (): number => {
  const env = process.env.CURSOR_MONITOR_INTERVAL;
  if (!env) {
    return DEFAULT_CURSOR_MONITOR_INTERVAL_MS;
  }
  const parsed = Number.parseInt(env, 10);
  if (Number.isNaN(parsed)) {
    return DEFAULT_CURSOR_MONITOR_INTERVAL_MS;
  }
  return clamp(parsed * 1000, 1000, 60 * 60 * 1000);
};

export const startCursorAutoInvocation = async (
  paths: Iterable<string>
): Promise<CursorAutoInvoker> => {
  if (!autoInvoker) {
    autoInvoker = new CursorAutoInvoker(getMonitorInterval());
  }
  await autoInvoker.start(paths);
  return autoInvoker;
};

export const stopCursorAutoInvocation = (): void => {
  autoInvoker?.stop();
  autoInvoker = undefined;
};

export const getAutoInvoker = (): CursorAutoInvoker | undefined => autoInvoker;

let activeAgentType: CursorAgentType | undefined;

const ensureAgentSelection = (type: CursorAgentType): void => {
  activeAgentType = type;
};

export const requireCursorAgent = (agentType: CursorAgentType) => {
  return <T extends (...args: unknown[]) => unknown>(handler: T): T => {
    const wrapped = ((...args: Parameters<T>) => {
      ensureAgentSelection(agentType);
      if (!autoInvoker || !autoInvoker.isRunning()) {
        throw new Error('Cursor auto-invocation is not active');
      }
      return handler(...args);
    }) as T;
    return wrapped;
  };
};

const evaluateCheck = (name: string, passed: boolean, message: string): CursorComplianceCheck => ({
  name,
  passed,
  message,
});

const REQUIRED_ENV_VARS = ['CURSOR_API_URL', 'CURSOR_API_KEY'];

const computeEnvChecks = (): CursorComplianceCheck[] => {
  return REQUIRED_ENV_VARS.map((name) => {
    const exists = Boolean(process.env[name]);
    const message = exists
      ? `${name} configured`
      : `${name} missing – set this variable to enable Cursor connectivity.`;
    return evaluateCheck(`env:${name.toLowerCase()}`, exists, message);
  });
};

const ensureSupportingServices = async (): Promise<void> => {
  if (!isMobileControlActive()) {
    await startMobileApp();
  }
  if (!isKnowledgeAutoLoaderActive()) {
    await startKnowledgeAutoLoading();
  }
  if (!isBrainBlocksActive()) {
    await startBrainBlocksIntegration();
  }
};

export const validateCursorCompliance = async (): Promise<CursorComplianceReport> => {
  await ensureSupportingServices();
  const checks: CursorComplianceCheck[] = [];
  const invokerActive = Boolean(autoInvoker && autoInvoker.isRunning());
  checks.push(
    evaluateCheck(
      'cursor:auto_invocation',
      invokerActive,
      invokerActive ? 'Auto invocation running' : 'Call startCursorAutoInvocation first.'
    )
  );

  const knowledgeActive = isKnowledgeAutoLoaderActive();
  checks.push(
    evaluateCheck(
      'knowledge:auto_loader',
      knowledgeActive,
      knowledgeActive ? 'Knowledge auto loader active' : 'Enable KNOWLEDGE_AUTO_LOAD=true.'
    )
  );

  const brainBlocks = isBrainBlocksActive();
  checks.push(
    evaluateCheck(
      'knowledge:brain_blocks',
      brainBlocks,
      brainBlocks ? 'Brain blocks integration active' : 'Start brain blocks integration.'
    )
  );

  const mobileActive = isMobileControlActive();
  checks.push(
    evaluateCheck(
      'mobile:control',
      mobileActive,
      mobileActive ? 'Mobile control active' : 'Start the mobile control service.'
    )
  );

  const agentSelected = Boolean(activeAgentType);
  checks.push(
    evaluateCheck(
      'cursor:agent_selected',
      agentSelected,
      agentSelected ? `Agent ${activeAgentType} selected` : 'Call requireCursorAgent in workflows.'
    )
  );

  checks.push(...computeEnvChecks());

  const passedChecks = checks.filter((check) => check.passed).length;
  const compliance = checks.length === 0 ? 1 : passedChecks / checks.length;

  const details = {
    agentType: activeAgentType ?? 'unassigned',
    watchedFiles: autoInvoker?.getTriggeredFiles().length ?? 0,
    knowledgeEntries: (await getKnowledgeEntries()).length,
    brainSections: (await getSections()).length,
    brainTags: (await getTags()).length,
    goals: (await getGoals()).length,
  };

  return {
    compliance,
    checks,
    details,
  };
};

export const enforceCursorIntegration = async (): Promise<void> => {
  const report = await validateCursorCompliance();
  const strict = (process.env.CURSOR_STRICT_MODE ?? 'true').toLowerCase() === 'true';
  if (strict && report.compliance < 1) {
    const failed = report.checks.filter((check) => !check.passed).map((check) => check.message);
    throw new Error(
      `Cursor compliance ${Math.round(report.compliance * 100)}% – ${failed.join('; ')}`
    );
  }
};

export const getAutoInvokerEvents = (): CursorInvocationEvent[] => {
  const invoker = autoInvoker;
  if (!invoker) {
    return [];
  }
  const lastInvocation = invoker.getLastInvocation();
  return invoker.getTriggeredFiles().map((filePath) => ({
    filePath,
    timestamp: lastInvocation ?? Date.now(),
  }));
};

export const getCursorAgentType = (): CursorAgentType | undefined => activeAgentType;

export type { CursorAutoInvoker, CursorInvocationEvent };
