import { cosineSimilarity, generateId, nowIso, type JsonValue } from '../shared/utils.js';
import type { ContextPacket, ContextRequest, ContextResponse } from '../shared/types.js';

const normaliseText = (text: string): string => text.replace(/\s+/g, ' ').trim();

const embed = (text: string): number[] => {
  const normalised = normaliseText(text.toLowerCase());
  const vector = new Array(16).fill(0);
  for (let i = 0; i < normalised.length; i += 1) {
    const code = normalised.charCodeAt(i);
    vector[i % vector.length] += code / 255;
  }
  return vector;
};

export class ContextFabric {
  private readonly packets = new Map<string, ContextPacket>();

  ingest(source: string, content: string, metadata: Record<string, JsonValue> = {}): ContextPacket {
    const summary = content.length > 160 ? `${content.slice(0, 157)}...` : content;
    const packet: ContextPacket = {
      id: generateId('ctx'),
      source,
      content,
      summary,
      embedding: embed(content),
      metadata,
      createdAt: nowIso(),
    };
    this.packets.set(packet.id, packet);
    return packet;
  }

  persist(packet: ContextPacket): void {
    this.packets.set(packet.id, packet);
  }

  retrieve(request: ContextRequest): ContextResponse {
    const scored = Array.from(this.packets.values()).map((packet) => ({
      packet,
      score: cosineSimilarity(
        packet.embedding,
        request.embedding ?? embed(request.keywords.join(' '))
      ),
    }));
    const selected = scored
      .filter((entry) => entry.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, request.limit)
      .map((entry) => entry.packet);
    return {
      packets: selected,
      rationale: selected.map((packet) => `Selected from ${packet.source}`),
    };
  }
}
