import crypto from 'node:crypto';

import type { TraceSpan } from '../shared/types.js';
import type { JsonValue } from '../shared/utils.js';

export class TracingService {
  private readonly spans = new Map<string, TraceSpan>();

  startSpan(name: string, attributes: Record<string, JsonValue> = {}): TraceSpan {
    const span: TraceSpan = {
      id: crypto.randomUUID(),
      name,
      startTime: Date.now(),
      attributes,
    };
    this.spans.set(span.id, span);
    return span;
  }

  endSpan(id: string, attributes: Record<string, JsonValue> = {}): TraceSpan | undefined {
    const span = this.spans.get(id);
    if (!span) return undefined;
    span.endTime = Date.now();
    Object.assign(span.attributes, attributes);
    return span;
  }

  getSpans(): TraceSpan[] {
    return Array.from(this.spans.values());
  }
}
