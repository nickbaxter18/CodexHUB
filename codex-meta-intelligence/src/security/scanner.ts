import type { SecurityFinding } from '../shared/types.js';

interface Dependency {
  name: string;
  version: string;
  severity?: 'low' | 'medium' | 'high';
}

export const scanDependencies = (dependencies: Dependency[]): SecurityFinding[] => {
  return dependencies
    .filter((dependency) => dependency.severity)
    .map((dependency) => ({
      severity: dependency.severity ?? 'low',
      category: 'dependency',
      message: `${dependency.name}@${dependency.version} has ${dependency.severity} severity advisories`,
      recommendation: 'Update to the latest patched version.',
    }));
};
