import type { JsonObject, JsonValue } from './utils.js';

export enum AgentRole {
  FRONTEND = 'frontend',
  BACKEND = 'backend',
  KNOWLEDGE = 'knowledge',
  QA = 'qa',
  REFINEMENT = 'refinement',
  OPERATOR = 'operator',
}

export type CursorAgentType = 'FRONTEND' | 'BACKEND' | 'KNOWLEDGE' | 'QA' | 'CICD' | 'ARCHITECT';

export interface AgentConfig {
  id: string;
  role: AgentRole;
  concurrency: number;
  timeoutMs: number;
  tools: string[];
}

export interface AgentGuidelines {
  environment: string[];
  testing: string[];
  coding: string[];
  logging: string[];
  pullRequests: string[];
}

export interface AgentMessage {
  taskId: string;
  macroId: string;
  payload: JsonValue;
  context: ContextPacket[];
  guidelines: AgentGuidelines;
  metadata: {
    priority: number;
    createdAt: string;
    source: string;
    version: string;
  };
}

export interface AgentResult {
  taskId: string;
  status: 'success' | 'error';
  summary: string;
  artifacts: Record<string, JsonValue>;
  issues: string[];
  contextUpdates: ContextPacket[];
  durationMs: number;
  error?: string;
}

export interface MacroStage {
  id: string;
  name: string;
  description: string;
  agentRole: AgentRole;
  retryLimit: number;
  continueOnError: boolean;
}

export interface MacroDefinition {
  name: string;
  description: string;
  stages: MacroStage[];
  fallbackMacro?: string;
  qualityThreshold: number;
}

export interface MacroContext {
  taskId: string;
  operatorId: string;
  input: JsonValue;
  metadata: Record<string, JsonValue>;
  guidelines: AgentGuidelines;
}

export interface MacroResult {
  taskId: string;
  macroName: string;
  stageResults: AgentResult[];
  success: boolean;
  startedAt: string;
  finishedAt: string;
}

export interface MetaTask {
  id: string;
  macroName: string;
  input: JsonValue;
  priority: number;
  owner: string;
  requestedAt: string;
}

export interface MetaStateSnapshot {
  queued: MetaTask[];
  running: MetaTask[];
  completed: MacroResult[];
  metrics: Record<string, number>;
}

export interface KnowledgeBlock {
  id: string;
  content: string;
  metadata: {
    author: string;
    timestamp: string;
    tags: string[];
    citations: string[];
    source: string;
    reliabilityScore: number;
  };
  links?: string[];
}

export interface KnowledgeQuery {
  keywords: string[];
  tags?: string[];
  limit?: number;
}

export interface KnowledgeResponse {
  blocks: Array<{ block: KnowledgeBlock; score: number }>;
}

export interface BrainBlock extends KnowledgeBlock {
  sections: string[];
  tags: string[];
}

export interface BrainBlockQuery {
  search?: string;
  tags?: string[];
}

export interface MemoryRecord {
  id: string;
  agentId: string;
  timestamp: string;
  dataType: string;
  payload: JsonValue;
  tags: string[];
  sensitivity?: 'public' | 'confidential' | 'restricted';
}

export interface LogEntry {
  taskId: string;
  actor: string;
  action: string;
  result: string;
  timestamp: string;
}

export interface CacheEntry<T> {
  key: string;
  value: T;
  expiresAt: number;
}

export interface QAIssue {
  engine: 'aesthetic' | 'technical' | 'narrative';
  severity: 'info' | 'warning' | 'error';
  message: string;
  affectedFiles?: string[];
}

export interface QAResult {
  success: boolean;
  issues: QAIssue[];
}

export interface ForecastResult {
  taskId: string;
  predictedDurationMs: number;
  confidence: number;
  notes: string[];
}

export interface RiskAssessment {
  taskId: string;
  riskScore: number;
  level: 'low' | 'medium' | 'high';
  factors: string[];
}

export interface ContextPacket {
  id: string;
  source: string;
  content: string;
  summary: string;
  embedding: number[];
  metadata: Record<string, JsonValue>;
  createdAt: string;
}

export interface ContextRequest {
  taskId: string;
  role: AgentRole;
  keywords: string[];
  limit: number;
  embedding?: number[];
}

export interface ContextResponse {
  packets: ContextPacket[];
  rationale: string[];
}

export interface GovernancePolicy {
  id: string;
  description: string;
  appliesTo: AgentRole[];
  validator: (packet: ContextPacket) => boolean;
}

export interface SecurityFinding {
  severity: 'low' | 'medium' | 'high';
  category: string;
  message: string;
  recommendation: string;
}

export interface MetricRecord {
  name: string;
  labels: Record<string, string>;
  value: number;
  timestamp: number;
}

export interface TraceSpan {
  id: string;
  name: string;
  startTime: number;
  endTime?: number;
  attributes: Record<string, JsonValue>;
}

export interface CursorComplianceCheck {
  name: string;
  passed: boolean;
  message: string;
}

export interface CursorComplianceReport {
  compliance: number;
  checks: CursorComplianceCheck[];
  details: Record<string, JsonValue>;
}

export interface MobileGoalInput {
  title: string;
  description: string;
  priority?: 'low' | 'medium' | 'high';
}

export interface MobileGoal {
  id: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high';
  status: 'pending' | 'approved' | 'completed';
  createdAt: string;
  updatedAt: string;
}

export type JsonSchema = JsonObject;
