import type { MetricRecord } from '../shared/types.js';

export class MetricsRegistry {
  private readonly metrics: MetricRecord[] = [];

  record(metric: MetricRecord): void {
    this.metrics.push(metric);
  }

  getMetrics(): MetricRecord[] {
    return [...this.metrics];
  }
}
