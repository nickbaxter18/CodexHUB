import { createWriteStream, existsSync, mkdirSync, statSync } from 'node:fs';
import path from 'node:path';

import type { LogEntry } from '../shared/types.js';
import { nowIso } from '../shared/utils.js';

const DEFAULT_MAX_SIZE = 512 * 1024;

export class RotatingLogger {
  private stream: ReturnType<typeof createWriteStream>;

  constructor(
    private readonly directory: string,
    private readonly maxSize = DEFAULT_MAX_SIZE
  ) {
    if (!existsSync(directory)) {
      mkdirSync(directory, { recursive: true });
    }
    this.stream = this.createStream();
  }

  log(entry: LogEntry): void {
    const payload = JSON.stringify({ ...entry, loggedAt: nowIso() });
    this.stream.write(`${payload}\n`);
    this.rotateIfNeeded();
  }

  private rotateIfNeeded(): void {
    const { size } = statSync(this.stream.path.toString());
    if (size < this.maxSize) {
      return;
    }
    this.stream.end();
    this.stream = this.createStream();
  }

  private createStream(): ReturnType<typeof createWriteStream> {
    const filePath = path.join(this.directory, `memory-${Date.now()}.log`);
    return createWriteStream(filePath, { flags: 'a', encoding: 'utf8' });
  }
}
