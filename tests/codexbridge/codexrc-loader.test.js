/**
 * CodexBridge configuration loader tests.
 */

import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { promises as fs } from 'fs';
import os from 'os';
import path from 'path';

import {
  loadCodexBridgeConfig,
  DEFAULT_CODEXBRIDGE_CONFIG,
  CodexRcConfigError
} from '../../codexbridge/src/codexrc-loader.js';

const SCHEMA_PATH = path.join(process.cwd(), 'codexbridge', 'schemas', 'codexrc.schema.json');

describe('CodexRcLoader', () => {
  /** @type {string} */
  let tmpDir;

  beforeEach(async () => {
    tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), 'codexrc-loader-'));
  });

  afterEach(async () => {
    if (tmpDir) {
      await fs.rm(tmpDir, { recursive: true, force: true });
    }
  });

  it('returns defaults when no configuration file is present', async () => {
    const { config, resolved, sourcePath, raw } = await loadCodexBridgeConfig({
      repoRoot: tmpDir,
      schemaPath: SCHEMA_PATH
    });
    assert.equal(sourcePath, null);
    assert.equal(raw, null);
    assert.deepEqual(config, DEFAULT_CODEXBRIDGE_CONFIG);
    assert.equal(resolved.repoRoot, tmpDir);
    assert.equal(
      resolved.plans.incomingDir,
      path.resolve(tmpDir, DEFAULT_CODEXBRIDGE_CONFIG.plans.incomingDir)
    );
    assert.equal(resolved.tests.defaultTimeoutSeconds, DEFAULT_CODEXBRIDGE_CONFIG.tests.defaultTimeoutSeconds);
  });

  it('merges overrides from .codexrc and resolves absolute paths', async () => {
    const override = {
      codexbridge: {
        plans: {
          incomingDir: 'custom/inbox'
        },
        macros: {
          typesImport: '@/macros/context',
          functionSuffix: 'Bridge'
        },
        cache: {
          macro: 'var/cache/macro.json',
          tests: 'var/cache/tests.json'
        },
        resultsDir: 'artifacts/results',
        tests: {
          defaultCommand: 'pnpm test',
          defaultTimeoutSeconds: 120
        }
      }
    };
    await fs.writeFile(path.join(tmpDir, '.codexrc'), JSON.stringify(override, null, 2));

    const { config, resolved, sourcePath } = await loadCodexBridgeConfig({
      repoRoot: tmpDir,
      schemaPath: SCHEMA_PATH
    });
    assert.ok(sourcePath?.endsWith('.codexrc'));
    assert.equal(config.plans.incomingDir, 'custom/inbox');
    assert.equal(config.macros.typesImport, '@/macros/context');
    assert.equal(config.macros.functionSuffix, 'Bridge');
    assert.equal(config.macros.typesSymbol, DEFAULT_CODEXBRIDGE_CONFIG.macros.typesSymbol);
    assert.equal(resolved.plans.incomingDir, path.resolve(tmpDir, 'custom/inbox'));
    assert.equal(resolved.resultsDir, path.resolve(tmpDir, 'artifacts/results'));
    assert.equal(resolved.cache.macro, path.resolve(tmpDir, 'var/cache/macro.json'));
    assert.equal(resolved.tests.defaultCommand, 'pnpm test');
  });

  it('throws descriptive errors when the configuration violates the schema', async () => {
    const invalid = {
      codexbridge: {
        tests: {
          defaultCommand: '',
          defaultTimeoutSeconds: 0
        }
      }
    };
    await fs.writeFile(path.join(tmpDir, '.codexrc'), JSON.stringify(invalid, null, 2));

    await assert.rejects(
      loadCodexBridgeConfig({ repoRoot: tmpDir, schemaPath: SCHEMA_PATH }),
      (error) =>
        error instanceof CodexRcConfigError &&
        Array.isArray(error.issues) &&
        error.issues.some((issue) => issue.includes('defaultTimeoutSeconds'))
    );
  });
});
