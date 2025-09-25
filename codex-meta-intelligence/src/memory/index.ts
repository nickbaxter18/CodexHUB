import type { MemoryRecord } from '../shared/types.js';
import { LruCache, generateId } from '../shared/utils.js';
import { DEFAULT_CACHE_CAPACITY } from '../shared/constants.js';

export class MemoryService {
  private readonly records = new Map<string, MemoryRecord>();

  private readonly indexByAgent = new Map<string, string[]>();

  private readonly cache = new LruCache<string, MemoryRecord>(DEFAULT_CACHE_CAPACITY);

  store(record: Omit<MemoryRecord, 'id'>): MemoryRecord {
    const entry: MemoryRecord = { ...record, id: generateId('memory') };
    this.records.set(entry.id, entry);
    this.cache.set(entry.id, entry);
    const agentRecords = this.indexByAgent.get(entry.agentId) ?? [];
    agentRecords.push(entry.id);
    this.indexByAgent.set(entry.agentId, agentRecords);
    return entry;
  }

  retrieve(id: string): MemoryRecord | undefined {
    return this.cache.get(id) ?? this.records.get(id);
  }

  queryByAgent(agentId: string): MemoryRecord[] {
    const ids = this.indexByAgent.get(agentId) ?? [];
    return ids
      .map((id) => this.retrieve(id))
      .filter((record): record is MemoryRecord => record !== undefined);
  }

  queryRange(start: Date, end: Date): MemoryRecord[] {
    return Array.from(this.records.values()).filter((record) => {
      const timestamp = new Date(record.timestamp).getTime();
      return timestamp >= start.getTime() && timestamp <= end.getTime();
    });
  }
}
