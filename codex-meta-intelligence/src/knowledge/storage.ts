import type { KnowledgeBlock, KnowledgeQuery, KnowledgeResponse } from '../shared/types.js';
import { clamp, generateId } from '../shared/utils.js';

export class InMemoryKnowledgeStore {
  private readonly blocks = new Map<string, KnowledgeBlock>();

  storeBlock(block: KnowledgeBlock): KnowledgeBlock {
    if (this.blocks.has(block.id)) {
      throw new Error(`Knowledge block with id ${block.id} already exists`);
    }
    this.blocks.set(block.id, block);
    return block;
  }

  createBlock(content: string, metadata: KnowledgeBlock['metadata']): KnowledgeBlock {
    const block: KnowledgeBlock = {
      id: generateId('kb'),
      content,
      metadata,
    };
    this.storeBlock(block);
    return block;
  }

  getBlock(id: string): KnowledgeBlock | undefined {
    return this.blocks.get(id);
  }

  search(query: KnowledgeQuery): KnowledgeResponse {
    const limit = clamp(query.limit ?? 10, 1, 50);
    const results = Array.from(this.blocks.values())
      .map((block) => ({ block, score: this.scoreBlock(block, query) }))
      .filter((entry) => entry.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, limit);
    return { blocks: results };
  }

  private scoreBlock(block: KnowledgeBlock, query: KnowledgeQuery): number {
    const keywordMatches = query.keywords.reduce((acc, keyword) => {
      const matches = block.content.toLowerCase().includes(keyword.toLowerCase()) ? 1 : 0;
      return acc + matches;
    }, 0);
    const tagMatches = (query.tags ?? []).reduce((acc, tag) => {
      return acc + (block.metadata.tags.includes(tag) ? 1 : 0);
    }, 0);
    return keywordMatches * 2 + tagMatches;
  }
}
