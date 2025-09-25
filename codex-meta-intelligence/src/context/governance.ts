import type { AgentRole, ContextPacket, GovernancePolicy } from '../shared/types.js';

const defaultPolicies: GovernancePolicy[] = [
  {
    id: 'sensitivity-public',
    description: 'Public packets are accessible to all agents.',
    appliesTo: [
      'frontend' as AgentRole,
      'backend' as AgentRole,
      'knowledge' as AgentRole,
      'qa' as AgentRole,
      'refinement' as AgentRole,
    ],
    validator: (packet) => packet.metadata['sensitivity'] !== 'restricted',
  },
];

export class Governance {
  private readonly policies: GovernancePolicy[];

  constructor(policies: GovernancePolicy[] = defaultPolicies) {
    this.policies = policies;
  }

  isAllowed(role: AgentRole, packet: ContextPacket): boolean {
    return this.policies
      .filter((policy) => policy.appliesTo.includes(role))
      .every((policy) => policy.validator(packet));
  }
}
