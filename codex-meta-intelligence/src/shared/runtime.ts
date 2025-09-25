import { MetricsRegistry } from '../analytics/metrics.js';
import { TracingService } from '../analytics/tracing.js';
import { ContextOrchestrator } from '../context/orchestrator.js';
import { KnowledgeService } from '../knowledge/index.js';
import { MemoryService } from '../memory/index.js';
import { QAEngine } from '../qa/index.js';

export const metricsRegistry = new MetricsRegistry();
export const tracingService = new TracingService();
export const contextOrchestrator = new ContextOrchestrator();
export const knowledgeService = new KnowledgeService();
export const memoryService = new MemoryService();
export const qaEngine = new QAEngine();
