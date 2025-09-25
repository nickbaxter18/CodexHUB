import { EventEmitter } from 'node:events';

import type { BrainBlock, BrainBlockQuery, KnowledgeBlock } from '../shared/types.js';
import { generateId } from '../shared/utils.js';
import {
  getKnowledgeEntries,
  isKnowledgeAutoLoaderActive,
  startKnowledgeAutoLoading,
} from './auto-loader.js';

interface BrainBlocksEvents {
  refresh: [BrainBlock[]];
}

const unique = <T>(values: Iterable<T>): T[] => Array.from(new Set(values));

const deriveSections = (block: KnowledgeBlock | BrainBlock): string[] => {
  const fromMetadata = block.metadata.tags
    .map((tag) => (tag.startsWith('section:') ? tag.slice('section:'.length) : undefined))
    .filter((section): section is string => Boolean(section));
  if (fromMetadata.length > 0) {
    return fromMetadata;
  }
  const headings = Array.from(block.content.matchAll(/^#+\s*(.+)$/gm)).map((match) => match[1]!);
  return headings.length > 0 ? headings : ['general'];
};

const createBrainBlock = (block: BrainBlock | KnowledgeBlock): BrainBlock => {
  return {
    ...block,
    id: block.id || generateId('brain'),
    sections:
      'sections' in block && block.sections?.length ? block.sections : deriveSections(block),
    tags: 'tags' in block && block.tags ? block.tags : unique([...block.metadata.tags]),
  };
};

class BrainBlocksIntegration extends EventEmitter<BrainBlocksEvents> {
  private blocks: BrainBlock[] = [];

  private active = false;

  async start(): Promise<void> {
    if (!isKnowledgeAutoLoaderActive()) {
      await startKnowledgeAutoLoading();
    }
    await this.refresh();
    this.active = true;
  }

  async refresh(): Promise<void> {
    const entries = await getKnowledgeEntries();
    this.blocks = entries.map((block) =>
      createBrainBlock({
        ...block,
        sections: block.links && block.links.length > 0 ? block.links : undefined,
      })
    );
    this.emit('refresh', this.blocks);
  }

  stop(): void {
    this.blocks = [];
    this.active = false;
  }

  isActive(): boolean {
    return this.active;
  }

  query(query: BrainBlockQuery = {}): BrainBlock[] {
    return this.blocks.filter((block) => {
      const matchesSearch = query.search
        ? block.content.toLowerCase().includes(query.search.toLowerCase())
        : true;
      const matchesTags = query.tags?.length
        ? query.tags.every((tag) => block.tags.includes(tag))
        : true;
      return matchesSearch && matchesTags;
    });
  }

  listSections(): string[] {
    return unique(this.blocks.flatMap((block) => block.sections));
  }

  listTags(): string[] {
    return unique(this.blocks.flatMap((block) => block.tags));
  }
}

let integration: BrainBlocksIntegration | undefined;

export const startBrainBlocksIntegration = async (): Promise<BrainBlocksIntegration> => {
  if (!integration) {
    integration = new BrainBlocksIntegration();
  }
  await integration.start();
  return integration;
};

export const stopBrainBlocksIntegration = (): void => {
  integration?.stop();
  integration = undefined;
};

export const queryBrainBlocks = async (query?: BrainBlockQuery): Promise<BrainBlock[]> => {
  if (!integration) {
    await startBrainBlocksIntegration();
  }
  return integration!.query(query);
};

export const getSections = async (): Promise<string[]> => {
  if (!integration) {
    await startBrainBlocksIntegration();
  }
  return integration!.listSections();
};

export const getTags = async (): Promise<string[]> => {
  if (!integration) {
    await startBrainBlocksIntegration();
  }
  return integration!.listTags();
};

export const isBrainBlocksActive = (): boolean => integration?.isActive() ?? false;

export type { BrainBlocksIntegration };
