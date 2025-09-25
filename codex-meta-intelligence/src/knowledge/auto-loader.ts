import { EventEmitter } from 'node:events';
import { readFile } from 'node:fs/promises';
import path from 'node:path';

import type { KnowledgeBlock } from '../shared/types.js';
import { generateId, nowIso } from '../shared/utils.js';
import { parseNdjson } from './scaffolds.js';

interface KnowledgeAutoLoaderEvents {
  reload: [KnowledgeBlock[]];
  error: [Error];
}

const DEFAULT_INTERVAL_MS =
  Number.parseInt(process.env.KNOWLEDGE_WATCH_INTERVAL ?? '30', 10) * 1000;

const getPathsFromEnv = (): string[] => {
  const env = process.env.KNOWLEDGE_NDJSON_PATHS ?? '';
  return env
    .split(',')
    .map((entry) => entry.trim())
    .filter(Boolean)
    .map((entry) => path.resolve(entry));
};

const normaliseBlocks = (blocks: KnowledgeBlock[]): KnowledgeBlock[] => {
  return blocks.map((block) => ({
    ...block,
    id: block.id || generateId('kb'),
    metadata: {
      ...block.metadata,
      timestamp: block.metadata.timestamp || nowIso(),
      tags: block.metadata.tags ?? [],
      citations: block.metadata.citations ?? [],
    },
    links: block.links ?? [],
  }));
};

class KnowledgeAutoLoader extends EventEmitter<KnowledgeAutoLoaderEvents> {
  private readonly entries = new Map<string, KnowledgeBlock>();

  private readonly intervalMs: number;

  private readonly paths: string[];

  private timer?: NodeJS.Timeout;

  private active = false;

  constructor(paths: string[], intervalMs: number) {
    super();
    this.paths = paths;
    this.intervalMs = intervalMs;
  }

  async start(): Promise<void> {
    if (this.active) {
      return;
    }
    await this.reload();
    if (this.paths.length > 0) {
      this.timer = setInterval(() => {
        void this.reload();
      }, this.intervalMs).unref();
    }
    this.active = true;
  }

  async stop(): Promise<void> {
    if (this.timer) {
      clearInterval(this.timer);
    }
    this.timer = undefined;
    this.active = false;
  }

  isActive(): boolean {
    return this.active;
  }

  getEntries(): KnowledgeBlock[] {
    return Array.from(this.entries.values());
  }

  private async reload(): Promise<void> {
    try {
      const loaded: KnowledgeBlock[] = [];
      for (const file of this.paths) {
        try {
          const raw = await readFile(file, 'utf8');
          const blocks = normaliseBlocks(parseNdjson(raw));
          for (const block of blocks) {
            this.entries.set(block.id, block);
            loaded.push(block);
          }
        } catch (error) {
          const err = error instanceof Error ? error : new Error(String(error));
          this.emit('error', err);
        }
      }
      this.emit('reload', loaded);
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      this.emit('error', err);
    }
  }
}

let loader: KnowledgeAutoLoader | undefined;

const shouldAutoLoad = (): boolean => {
  const env = process.env.KNOWLEDGE_AUTO_LOAD ?? 'false';
  return env.toLowerCase() === 'true';
};

export const startKnowledgeAutoLoading = async (
  paths: string[] = getPathsFromEnv(),
  intervalMs = DEFAULT_INTERVAL_MS
): Promise<KnowledgeAutoLoader> => {
  if (!loader) {
    loader = new KnowledgeAutoLoader(paths, intervalMs);
  }
  if (shouldAutoLoad()) {
    await loader.start();
  }
  return loader;
};

export const stopKnowledgeAutoLoading = async (): Promise<void> => {
  if (loader) {
    await loader.stop();
  }
  loader = undefined;
};

export const getKnowledgeEntries = async (): Promise<KnowledgeBlock[]> => {
  if (!loader) {
    return [];
  }
  if (!loader.isActive()) {
    await loader.start();
  }
  return loader.getEntries();
};

export const isKnowledgeAutoLoaderActive = (): boolean => {
  return loader?.isActive() ?? false;
};

export type { KnowledgeAutoLoader };
