import type { KnowledgeBlock, KnowledgeQuery, KnowledgeResponse } from '../shared/types.js';
import { InMemoryKnowledgeStore } from './storage.js';
import { validateKnowledgeBlock } from './scaffolds.js';

export class KnowledgeService {
  constructor(private readonly store = new InMemoryKnowledgeStore()) {}

  storeBlock(block: KnowledgeBlock): KnowledgeBlock {
    validateKnowledgeBlock(block);
    return this.store.storeBlock(block);
  }

  ingestBlocks(blocks: KnowledgeBlock[]): KnowledgeBlock[] {
    return blocks.map((block) => this.storeBlock(block));
  }

  fetchBlock(id: string): KnowledgeBlock | undefined {
    return this.store.getBlock(id);
  }

  queryKnowledge(query: KnowledgeQuery): KnowledgeResponse {
    return this.store.search(query);
  }
}
