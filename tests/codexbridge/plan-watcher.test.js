/**
 * CodexBridge plan watcher integration tests.
 */

import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { promises as fs } from 'fs';
import os from 'os';
import path from 'path';

import PlanWatcher from '../../codexbridge/src/plan-watcher.js';
import PlanValidator from '../../codexbridge/src/plan-validator.js';

const SCHEMA_PATH = path.join(process.cwd(), 'codexbridge', 'schemas', 'plan.schema.json');

const BASE_PLAN = {
  macro: '::frontend.dashboard',
  description: 'Generate dashboard widgets with live data bindings.',
  domain: 'frontend',
  created_at: '2025-09-23T14:00:00Z',
  inputs: [
    {
      name: 'context',
      type: 'MacroContext',
      description: 'Codex macro execution context.'
    }
  ],
  safe: true,
  requires_review: false
};

describe('PlanWatcher', () => {
  /** @type {string} */
  let tmpDir;

  beforeEach(async () => {
    tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), 'codexbridge-watcher-'));
    await fs.mkdir(path.join(tmpDir, 'plans', 'from_gpt'), { recursive: true });
    await fs.mkdir(path.join(tmpDir, 'plans', 'processed'), { recursive: true });
    await fs.mkdir(path.join(tmpDir, 'plans', 'rejected'), { recursive: true });
    await fs.mkdir(path.join(tmpDir, 'macros'), { recursive: true });
    await fs.mkdir(path.join(tmpDir, 'cache'), { recursive: true });
    await fs.mkdir(path.join(tmpDir, 'results'), { recursive: true });

    await fs.writeFile(
      path.join(tmpDir, 'macros', 'registry.json'),
      JSON.stringify({ version: 1, macros: [] }, null, 2)
    );
    await fs.writeFile(path.join(tmpDir, 'cache', 'macro_output.json'), JSON.stringify({}, null, 2));
    await fs.writeFile(
      path.join(tmpDir, 'cache', 'test_outcomes.json'),
      JSON.stringify({}, null, 2)
    );
  });

  afterEach(async () => {
    if (tmpDir) {
      await fs.rm(tmpDir, { recursive: true, force: true });
    }
  });

  it('processes a safe plan, generates macro stubs, and archives metadata', async () => {
    const planFile = path.join(tmpDir, 'plans', 'from_gpt', '2025-09-23__dashboard.json');
    const planPayload = {
      ...BASE_PLAN,
      tests: [
        {
          type: 'unit',
          command: 'npm test',
          description: 'Run primary unit tests.'
        }
      ],
      dependencies: [],
      governance: {
        policy_refs: ['AGENT-SAFE-MACROS']
      }
    };
    await fs.writeFile(planFile, JSON.stringify(planPayload, null, 2));

    const commandInvocations = [];
    const watcher = new PlanWatcher({
      repoRoot: tmpDir,
      validator: new PlanValidator({ schemaPath: SCHEMA_PATH }),
      runCommand: async (command, options) => {
        commandInvocations.push({ command, options });
        return { stdout: 'ok', stderr: '' };
      }
    });

    const outcomes = await watcher.processPendingPlans();
    assert.equal(outcomes.length, 1);
    assert.equal(outcomes[0].status, 'processed');
    assert.ok(outcomes[0].macroPath?.endsWith('dashboard.ts'));

    assert.equal(commandInvocations.length, 1);
    assert.equal(commandInvocations[0].command, 'npm test');

    const macroPath = path.join(tmpDir, 'macros', 'frontend', 'dashboard.ts');
    const macroContent = await fs.readFile(macroPath, 'utf-8');
    assert.ok(macroContent.includes('Macro Identifier: ::frontend.dashboard'));
    assert.ok(macroContent.includes("Macro ::frontend.dashboard is not implemented yet."));

    const registry = JSON.parse(
      await fs.readFile(path.join(tmpDir, 'macros', 'registry.json'), 'utf-8')
    );
    assert.equal(registry.macros.length, 1);
    assert.equal(registry.macros[0].identifier, planPayload.macro);

    const processedPlan = JSON.parse(
      await fs.readFile(path.join(tmpDir, 'plans', 'processed', '2025-09-23__dashboard.json'), 'utf-8')
    );
    assert.equal(processedPlan.codexbridge.status, 'processed');
    assert.ok(processedPlan.codexbridge.tests.length > 0);

    const macroCache = JSON.parse(
      await fs.readFile(path.join(tmpDir, 'cache', 'macro_output.json'), 'utf-8')
    );
    assert.ok(macroCache.macros['::frontend.dashboard']);

    const testCache = JSON.parse(
      await fs.readFile(path.join(tmpDir, 'cache', 'test_outcomes.json'), 'utf-8')
    );
    assert.ok(testCache.macros['::frontend.dashboard']);

    const resultsFiles = await fs.readdir(path.join(tmpDir, 'results'));
    assert.equal(resultsFiles.length, 1);
    assert.ok(resultsFiles[0].includes('processed'));
  });

  it('reroutes unsafe plans to the rejected inbox with diagnostics', async () => {
    const planFile = path.join(tmpDir, 'plans', 'from_gpt', '2025-09-24__dashboard.json');
    const planPayload = {
      ...BASE_PLAN,
      requires_review: true
    };
    await fs.writeFile(planFile, JSON.stringify(planPayload, null, 2));

    const commandInvocations = [];
    const watcher = new PlanWatcher({
      repoRoot: tmpDir,
      validator: new PlanValidator({ schemaPath: SCHEMA_PATH }),
      runCommand: async (command, options) => {
        commandInvocations.push({ command, options });
        return { stdout: 'ok', stderr: '' };
      }
    });

    const outcomes = await watcher.processPendingPlans();
    assert.equal(outcomes[0].status, 'rejected');
    assert.match(outcomes[0].reason ?? '', /manual review/i);
    assert.equal(commandInvocations.length, 0);

    const rejectedPlan = JSON.parse(
      await fs.readFile(path.join(tmpDir, 'plans', 'rejected', '2025-09-24__dashboard.json'), 'utf-8')
    );
    assert.equal(rejectedPlan.codexbridge.status, 'rejected');
    assert.ok(rejectedPlan.codexbridge.issues.length >= 0);

    const macroExists = await fs
      .access(path.join(tmpDir, 'macros', 'frontend', 'dashboard.ts'))
      .then(() => true)
      .catch(() => false);
    assert.equal(macroExists, false);

    const resultsFiles = await fs.readdir(path.join(tmpDir, 'results'));
    assert.equal(resultsFiles.length, 1);
    assert.ok(resultsFiles[0].includes('rejected'));
  });
});
