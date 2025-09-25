import type { AgentRole, ContextPacket, ContextRequest, ContextResponse } from '../shared/types.js';
import type { JsonValue } from '../shared/utils.js';
import { ContextFabric } from './fabric.js';
import { Governance } from './governance.js';

export class ContextOrchestrator {
  private readonly fabric: ContextFabric;

  private readonly governance: Governance;

  constructor(fabric = new ContextFabric(), governance = new Governance()) {
    this.fabric = fabric;
    this.governance = governance;
  }

  ingest(source: string, content: string, metadata: Record<string, JsonValue> = {}): ContextPacket {
    return this.fabric.ingest(source, content, metadata);
  }

  retrieve(request: ContextRequest): ContextResponse {
    const response = this.fabric.retrieve(request);
    const filtered = response.packets.filter((packet) =>
      this.governance.isAllowed(request.role, packet)
    );
    return {
      packets: filtered,
      rationale: filtered.map((packet) => `Allowed for ${request.role} from ${packet.source}`),
    };
  }

  compose(role: AgentRole, packets: ContextPacket[]): string {
    const allowed = packets.filter((packet) => this.governance.isAllowed(role, packet));
    return allowed.map((packet) => packet.summary).join('\n');
  }
}
