import { readFile } from 'node:fs/promises';
import path from 'node:path';

import merge from 'lodash.merge';

import type { AgentGuidelines } from '../shared/types.js';

const defaultGuidelines: AgentGuidelines = {
  environment: [],
  testing: [],
  coding: [],
  logging: [],
  pullRequests: [],
};

const sectionMatchers: Record<keyof AgentGuidelines, RegExp> = {
  environment: /##\s+Environment Setup/i,
  testing: /##\s+Testing[^\n]*/i,
  coding: /##\s+Coding[^\n]*/i,
  logging: /##\s+Logging[^\n]*/i,
  pullRequests: /##\s+Pull Request[^\n]*/i,
};

const bulletPatterns = [/^[-*]\s+/, /^\d+\.\s+/];

const normaliseSources = (source?: string | string[]): string[] => {
  if (!source) return [process.cwd()];
  return (Array.isArray(source) ? source : [source]).filter((value) => value.trim().length > 0);
};

export class AgentGuidelineReader {
  private readonly cache = new Map<string, AgentGuidelines>();

  constructor(private readonly projectRoot: string = process.cwd()) {}

  async mergeGuidelines(source?: string | string[]): Promise<AgentGuidelines> {
    const sources = normaliseSources(source).map((value) =>
      path.isAbsolute(value) ? value : path.join(this.projectRoot, value)
    );
    const directories = sources.flatMap((candidate) => this.collectDirectories(candidate));
    let merged: AgentGuidelines = merge({}, defaultGuidelines);
    for (const directory of directories) {
      const filePath = await this.resolveAgentsFile(directory);
      if (!filePath) continue;
      const cached = this.cache.get(filePath);
      const parsed = cached ?? (await this.parseFile(filePath));
      this.cache.set(filePath, parsed);
      merged = this.mergeGuidelineObjects(merged, parsed);
    }
    return merged;
  }

  private collectDirectories(targetPath: string): string[] {
    const directories: string[] = [];
    let current = path.extname(targetPath) ? path.dirname(targetPath) : targetPath;
    const stopAt = path.resolve(this.projectRoot);
    while (current && !directories.includes(current)) {
      directories.unshift(current);
      if (path.resolve(current) === stopAt) {
        break;
      }
      const parent = path.dirname(current);
      if (parent === current) {
        break;
      }
      current = parent;
    }
    return directories;
  }

  private async resolveAgentsFile(directory: string): Promise<string | undefined> {
    const candidates = ['AGENTS.md', 'CODEX.md'];
    for (const candidate of candidates) {
      const filePath = path.join(directory, candidate);
      try {
        await readFile(filePath);
        return filePath;
      } catch (error) {
        if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
          continue;
        }
        throw error;
      }
    }
    return undefined;
  }

  private async parseFile(filePath: string): Promise<AgentGuidelines> {
    const content = await readFile(filePath, 'utf8');
    const result: AgentGuidelines = merge({}, defaultGuidelines);
    for (const [key, matcher] of Object.entries(sectionMatchers)) {
      const section = this.extractSection(content, matcher);
      if (!section) continue;
      const lines = this.extractEntries(section);
      (result as AgentGuidelines)[key as keyof AgentGuidelines] = lines;
    }
    return result;
  }

  private extractEntries(section: string): string[] {
    const entries: string[] = [];
    const seen = new Set<string>();
    let inFence = false;
    const fenceBuffer: string[] = [];
    const pushValue = (value: string) => {
      const trimmed = value.trim();
      if (!trimmed) return;
      if (seen.has(trimmed)) return;
      seen.add(trimmed);
      entries.push(trimmed);
    };
    for (const rawLine of section.split('\n')) {
      const line = rawLine.trimEnd();
      if (line.trim().startsWith('```')) {
        if (inFence) {
          pushValue(fenceBuffer.join('\n'));
          fenceBuffer.length = 0;
        }
        inFence = !inFence;
        continue;
      }
      if (inFence) {
        fenceBuffer.push(rawLine);
        continue;
      }
      const trimmed = line.trim();
      if (!trimmed) continue;
      if (/^#{2,}\s+/u.test(trimmed)) {
        continue;
      }
      const pattern = bulletPatterns.find((regex) => regex.test(trimmed));
      if (pattern) {
        pushValue(trimmed.replace(pattern, ''));
        continue;
      }
      pushValue(trimmed);
    }
    if (fenceBuffer.length > 0) {
      pushValue(fenceBuffer.join('\n'));
    }
    return entries;
  }

  private extractSection(content: string, matcher: RegExp): string | undefined {
    const headingMatch = content.match(matcher);
    if (!headingMatch) return undefined;
    const startIndex = headingMatch.index ?? 0;
    const remaining = content.slice(startIndex);
    const nextHeading = remaining.search(/\n##\s+/);
    if (nextHeading === -1) return remaining;
    return remaining.slice(0, nextHeading);
  }

  private mergeGuidelineObjects(base: AgentGuidelines, update: AgentGuidelines): AgentGuidelines {
    const merged = merge({}, base);
    for (const key of Object.keys(update) as Array<keyof AgentGuidelines>) {
      const current = merged[key] ?? [];
      const incoming = update[key] ?? [];
      const ordered = [...current];
      const seen = new Set(current);
      for (const entry of incoming) {
        if (seen.has(entry)) continue;
        seen.add(entry);
        ordered.push(entry);
      }
      merged[key] = ordered;
    }
    return merged;
  }
}
