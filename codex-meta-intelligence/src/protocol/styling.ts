interface StylingIssue {
  rule: string;
  message: string;
  severity: 'info' | 'warning' | 'error';
}

interface StylingDocument {
  palette: Array<{ name: string; contrastRatio: number }>;
  typographyScale: number[];
  motionDensity: number;
}

export const validateStyling = (document: StylingDocument): StylingIssue[] => {
  const issues: StylingIssue[] = [];
  for (const colour of document.palette) {
    if (colour.contrastRatio < 4.5) {
      issues.push({
        rule: 'contrast',
        message: `${colour.name} contrast ratio below 4.5:1`,
        severity: 'error',
      });
    }
  }
  if (document.typographyScale.length < 3) {
    issues.push({
      rule: 'typography-scale',
      message: 'Typography scale should provide at least three steps for hierarchy.',
      severity: 'warning',
    });
  }
  if (document.motionDensity > 0.6) {
    issues.push({
      rule: 'motion-density',
      message: 'Motion density is high; consider reducing animations for accessibility.',
      severity: 'warning',
    });
  }
  return issues;
};

export type { StylingDocument, StylingIssue };
