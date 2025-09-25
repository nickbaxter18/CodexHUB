import crypto from 'node:crypto';

export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonObject | JsonArray;
export interface JsonObject {
  [key: string]: JsonValue;
}
export interface JsonArray extends Array<JsonValue> {}

export const nowIso = (): string => new Date().toISOString();

export const generateId = (prefix = 'id'): string => `${prefix}_${crypto.randomUUID()}`;

export const deepFreeze = <T>(value: T): T => {
  if (typeof value !== 'object' || value === null) {
    return value;
  }
  Object.freeze(value);
  for (const key of Object.getOwnPropertyNames(value)) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const property = (value as any)[key];
    if (property && typeof property === 'object' && !Object.isFrozen(property)) {
      deepFreeze(property);
    }
  }
  return value;
};

export const cosineSimilarity = (a: number[], b: number[]): number => {
  if (a.length !== b.length || a.length === 0) {
    return 0;
  }
  let dot = 0;
  let magA = 0;
  let magB = 0;
  for (let i = 0; i < a.length; i += 1) {
    const ai = a[i]!;
    const bi = b[i]!;
    dot += ai * bi;
    magA += ai ** 2;
    magB += bi ** 2;
  }
  if (magA === 0 || magB === 0) {
    return 0;
  }
  return dot / (Math.sqrt(magA) * Math.sqrt(magB));
};

export const clamp = (value: number, min: number, max: number): number => {
  if (value < min) return min;
  if (value > max) return max;
  return value;
};

export const normaliseWeights = (weights: number[]): number[] => {
  const total = weights.reduce((acc, value) => acc + value, 0);
  if (total === 0) {
    return weights.map(() => 0);
  }
  return weights.map((value) => value / total);
};

export class LruCache<K, V> {
  private readonly capacity: number;

  private readonly map = new Map<K, { value: V; expiresAt?: number }>();

  constructor(capacity: number) {
    if (capacity <= 0) {
      throw new Error('LRU cache capacity must be positive');
    }
    this.capacity = capacity;
  }

  get(key: K): V | undefined {
    const entry = this.map.get(key);
    if (!entry) {
      return undefined;
    }
    if (entry.expiresAt && entry.expiresAt < Date.now()) {
      this.map.delete(key);
      return undefined;
    }
    this.map.delete(key);
    this.map.set(key, entry);
    return entry.value;
  }

  set(key: K, value: V, ttlMs?: number): void {
    if (this.map.has(key)) {
      this.map.delete(key);
    }
    if (this.map.size >= this.capacity) {
      const { value: oldestKey, done } = this.map.keys().next();
      if (!done && oldestKey !== undefined) {
        this.map.delete(oldestKey);
      }
    }
    this.map.set(key, { value, expiresAt: ttlMs ? Date.now() + ttlMs : undefined });
  }

  has(key: K): boolean {
    return this.get(key) !== undefined;
  }

  clear(): void {
    this.map.clear();
  }
}
