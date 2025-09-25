interface Proposal {
  id: string;
  priority: number;
  confidence: number;
  content: string;
  timestamp: number;
}

interface HarmonyResult {
  accepted: Proposal;
  rejected: Proposal[];
}

export const resolveConflict = (proposals: Proposal[]): HarmonyResult => {
  if (proposals.length === 0) {
    throw new Error('No proposals provided for harmony resolution');
  }
  const sorted = [...proposals].sort((a, b) => {
    if (a.priority !== b.priority) return b.priority - a.priority;
    if (a.confidence !== b.confidence) return b.confidence - a.confidence;
    return b.timestamp - a.timestamp;
  });
  const [accepted, ...rest] = sorted as [Proposal, ...Proposal[]];
  return { accepted, rejected: rest };
};

export type { Proposal as HarmonyProposal, HarmonyResult };
