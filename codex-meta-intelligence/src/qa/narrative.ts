import type { QAIssue } from '../shared/types.js';

interface NarrativeAnalysis {
  tone: 'neutral' | 'enthusiastic' | 'formal' | 'empathetic';
  coherenceScore: number;
  fairnessScore: number;
}

export const runNarrativeChecks = (analysis: NarrativeAnalysis): QAIssue[] => {
  const issues: QAIssue[] = [];
  if (analysis.coherenceScore < 0.7) {
    issues.push({
      engine: 'narrative',
      severity: 'warning',
      message: 'Narrative coherence below threshold',
    });
  }
  if (analysis.fairnessScore < 0.8) {
    issues.push({
      engine: 'narrative',
      severity: 'warning',
      message: 'Fairness score below recommended minimum',
    });
  }
  if (analysis.tone === 'formal') {
    issues.push({
      engine: 'narrative',
      severity: 'info',
      message: 'Tone is formal; consider adding warmth for user-facing content',
    });
  }
  return issues;
};
