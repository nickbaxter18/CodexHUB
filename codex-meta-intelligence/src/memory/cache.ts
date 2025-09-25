import { LruCache } from '../shared/utils.js';

export class MemoryCache<T> {
  private readonly cache: LruCache<string, T>;

  constructor(capacity: number) {
    this.cache = new LruCache<string, T>(capacity);
  }

  get(key: string): T | undefined {
    return this.cache.get(key);
  }

  set(key: string, value: T, ttlMs?: number): void {
    this.cache.set(key, value, ttlMs);
  }

  has(key: string): boolean {
    return this.cache.has(key);
  }

  clear(): void {
    this.cache.clear();
  }
}
