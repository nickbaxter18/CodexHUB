/**
 * CodexBridge plan validator tests.
 */

import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { promises as fs } from 'fs';
import os from 'os';
import path from 'path';

import PlanValidator, { PlanValidationError } from '../../codexbridge/src/plan-validator.js';

const SAMPLE_PLAN = {
  macro: '::frontend.dashboard',
  description: 'Generate dashboard widgets with live data bindings.',
  domain: 'frontend',
  created_at: '2025-09-23T14:00:00Z',
  inputs: [
    {
      name: 'context',
      type: 'MacroContext',
      description: 'Codex macro execution context.'
    },
    {
      name: 'widgetCount',
      type: 'number',
      description: 'Number of widgets to scaffold.',
      required: false,
      default: 4
    }
  ],
  safe: true,
  requires_review: false,
  tests: [
    {
      type: 'unit',
      command: 'npm test',
      description: 'Run existing unit tests.'
    }
  ],
  dependencies: ['::shared.theme'],
  governance: {
    policy_refs: ['AGENT-SAFE-MACROS'],
    escalation_path: 'Notify QA channel'
  },
  notes: 'Ensure theming tokens use the neutral palette.'
};

describe('PlanValidator', () => {
  /** @type {PlanValidator} */
  let validator;

  beforeEach(() => {
    validator = new PlanValidator();
  });

  it('validates a conforming plan', async () => {
    const result = await validator.validate(SAMPLE_PLAN);
    assert.equal(result.valid, true);
    assert.ok(!result.errors);
  });

  it('rejects plans with additional properties', async () => {
    const invalidPlan = { ...SAMPLE_PLAN, extraneous: true };
    const result = await validator.validate(invalidPlan);
    assert.equal(result.valid, false);
    assert.ok(result.errors?.some((message) => message.includes('Unexpected property')));
  });

  it('throws descriptive errors for invalid files', async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), 'codexbridge-plan-'));
    const filePath = path.join(tmpDir, 'plan.json');
    await fs.writeFile(filePath, '{"macro":');

    try {
      await assert.rejects(
        validator.validateFile(filePath),
        (error) => error instanceof PlanValidationError
      );
    } finally {
      await fs.rm(tmpDir, { recursive: true, force: true });
    }
  });

  it('detects when automation must be gated', async () => {
    const gate = validator.getAutomationGate(SAMPLE_PLAN);
    assert.deepEqual(gate, { autoExecutable: true });

    const unsafeGate = validator.getAutomationGate({ ...SAMPLE_PLAN, safe: false });
    assert.equal(unsafeGate.autoExecutable, false);
    assert.ok(unsafeGate.reason.includes('unsafe'));

    const reviewGate = validator.getAutomationGate({ ...SAMPLE_PLAN, requires_review: true });
    assert.equal(reviewGate.autoExecutable, false);
    assert.ok(reviewGate.reason.includes('manual review'));
  });
});
