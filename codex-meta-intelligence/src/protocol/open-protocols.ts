import crypto from 'node:crypto';

interface McpTool {
  name: string;
  description: string;
  schema: object;
}

interface AcpEnvelope<T = unknown> {
  sender: string;
  recipient: string;
  protocolVersion: string;
  conversationId: string;
  timestamp: string;
  payload: T;
  signature?: string;
}

interface AgentRegistration {
  id: string;
  role: string;
  capabilities: string[];
  endpoint: string;
}

const signEnvelope = (envelope: AcpEnvelope, secret: string): string => {
  const hmac = crypto.createHmac('sha256', secret);
  hmac.update(JSON.stringify({ ...envelope, signature: undefined }));
  return hmac.digest('hex');
};

export const createMcpToolRegistry = (tools: McpTool[]): Map<string, McpTool> => {
  const registry = new Map<string, McpTool>();
  for (const tool of tools) {
    registry.set(tool.name, tool);
  }
  return registry;
};

export const createAcpEnvelope = <T>(
  payload: T,
  sender: string,
  recipient: string,
  secret?: string
): AcpEnvelope<T> => {
  const envelope: AcpEnvelope<T> = {
    sender,
    recipient,
    protocolVersion: '1.0.0',
    conversationId: crypto.randomUUID(),
    timestamp: new Date().toISOString(),
    payload,
  };
  if (secret) {
    envelope.signature = signEnvelope(envelope, secret);
  }
  return envelope;
};

export const verifyAcpEnvelope = (envelope: AcpEnvelope, secret: string): boolean => {
  if (!envelope.signature) return false;
  const expected = signEnvelope(envelope, secret);
  return envelope.signature === expected;
};

export const registerAgent = (
  registry: Map<string, AgentRegistration>,
  registration: AgentRegistration
): void => {
  registry.set(registration.id, registration);
};

export const listAgents = (registry: Map<string, AgentRegistration>): AgentRegistration[] => {
  return Array.from(registry.values());
};
