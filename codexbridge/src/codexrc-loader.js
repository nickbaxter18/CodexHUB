/**
 * ==========================================================================
 * Header & Purpose
 * ==========================================================================
 * Module Name: codexbridge/src/codexrc-loader.js
 * Responsibility: Load and validate the `.codexrc` configuration that governs
 *                 CodexBridge runtime behaviour, ensuring repository owners
 *                 can declaratively customise plan ingestion, macro generation,
 *                 caching, and testing semantics.
 * Why it matters: Centralising configuration in a validated schema prevents
 *                 drift between environments, enables governance auditing, and
 *                 unlocks automation by allowing planners to rely on consistent
 *                 directory layouts and execution policies.
 */

// ==========================================================================
// Imports / Dependencies
// ==========================================================================
import { promises as fs } from 'fs';
import path from 'path';
import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';

// ==========================================================================
// Types / Interfaces / Schemas (JSDoc based for tooling support)
// ==========================================================================
/**
 * @typedef {Object} CodexBridgeConfig
 * @property {{incomingDir: string, processedDir: string, rejectedDir: string}} plans
 * @property {{rootDir: string, registryPath: string, typesImport: string|null, typesSymbol: string, functionSuffix: string}} macros
 * @property {string} resultsDir
 * @property {{macro: string, tests: string}} cache
 * @property {{defaultCommand: string, defaultTimeoutSeconds: number}} tests
 */

/**
 * @typedef {Object} LoadedCodexBridgeConfig
 * @property {CodexBridgeConfig} config - Merged configuration with defaults applied.
 * @property {{repoRoot: string, plans: CodexBridgeConfig['plans'], macros: CodexBridgeConfig['macros'] & {registryPath: string}, cache: CodexBridgeConfig['cache'], resultsDir: string, tests: CodexBridgeConfig['tests']}} resolved
 *   - Absolute-path variants of relevant fields, ready for runtime consumption.
 * @property {string|null} sourcePath - Location of the loaded configuration file or null when defaults were used.
 * @property {object|null} raw - Raw JSON payload read from disk (when present).
 */

/**
 * @typedef {Object} CodexRcLoaderOptions
 * @property {string} [repoRoot]
 * @property {string} [configPath]
 * @property {string} [schemaPath]
 * @property {import('ajv').default} [ajv]
 * @property {string[]} [configCandidates]
 */

// ==========================================================================
// Default Configuration
// ==========================================================================
export const DEFAULT_CODEXBRIDGE_CONFIG = Object.freeze({
  plans: Object.freeze({
    incomingDir: 'plans/from_gpt',
    processedDir: 'plans/processed',
    rejectedDir: 'plans/rejected'
  }),
  macros: Object.freeze({
    rootDir: 'macros',
    registryPath: 'macros/registry.json',
    typesImport: null,
    typesSymbol: 'MacroContext',
    functionSuffix: 'Macro'
  }),
  resultsDir: 'results',
  cache: Object.freeze({
    macro: 'cache/macro_output.json',
    tests: 'cache/test_outcomes.json'
  }),
  tests: Object.freeze({
    defaultCommand: 'npm test',
    defaultTimeoutSeconds: 600
  })
});

// ==========================================================================
// Error & Edge Handling Utilities
// ==========================================================================
export class CodexRcConfigError extends Error {
  /**
   * @param {string} message
   * @param {string[]} [issues]
   */
  constructor(message, issues = []) {
    super(message);
    this.name = 'CodexRcConfigError';
    this.issues = issues;
  }
}

// ==========================================================================
// Core Logic / Implementation
// ==========================================================================
export class CodexRcLoader {
  /**
   * @param {CodexRcLoaderOptions} [options]
   */
  constructor(options = {}) {
    this.repoRoot = options.repoRoot ?? process.cwd();
    const defaultCandidates = ['.codexrc', '.codexrc.json', 'codexrc.json'];
    if (options.configPath) {
      defaultCandidates.unshift(options.configPath);
    }
    this.configCandidates = options.configCandidates ?? Array.from(new Set(defaultCandidates));
    this.schemaPath = options.schemaPath ?? path.join(
      this.repoRoot,
      'codexbridge',
      'schemas',
      'codexrc.schema.json'
    );
    this.ajv = options.ajv ?? this.#createAjvInstance();
    this.compiledValidator = null;
    this.schema = null;
  }

  /**
   * Creates an Ajv instance tailored for configuration validation.
   * @returns {Ajv}
   */
  #createAjvInstance() {
    const ajv = new Ajv2020({
      strict: false,
      allErrors: true,
      allowUnionTypes: true,
      coerceTypes: false,
      removeAdditional: false
    });
    addFormats(ajv);
    return ajv;
  }

  /**
   * Loads the configuration from disk, applies defaults, and resolves paths.
   * @returns {Promise<LoadedCodexBridgeConfig>}
   */
  async load() {
    const configPath = await this.#resolveConfigPath();
    if (!configPath) {
      const config = this.#clone(DEFAULT_CODEXBRIDGE_CONFIG);
      return {
        config,
        resolved: this.#resolvePaths(config),
        sourcePath: null,
        raw: null
      };
    }

    const rawContent = await fs.readFile(configPath, 'utf-8');
    let parsed;
    try {
      parsed = JSON.parse(rawContent);
    } catch (error) {
      throw new CodexRcConfigError(`Unable to parse configuration JSON: ${configPath}`, [
        error instanceof Error ? error.message : 'Unknown configuration parse error'
      ]);
    }

    await this.#assertValid(parsed, configPath);

    const overrides = parsed?.codexbridge ?? {};
    const config = this.#mergeConfig(overrides);
    return {
      config,
      resolved: this.#resolvePaths(config),
      sourcePath: configPath,
      raw: parsed
    };
  }

  /**
   * Determines the actual configuration file path to load.
   * @returns {Promise<string|null>}
   */
  async #resolveConfigPath() {
    for (const candidate of this.configCandidates) {
      if (!candidate) {
        continue;
      }
      const absolute = path.isAbsolute(candidate)
        ? candidate
        : path.join(this.repoRoot, candidate);
      try {
        const stat = await fs.stat(absolute);
        if (stat.isFile()) {
          return absolute;
        }
      } catch (error) {
        if ((/** @type {NodeJS.ErrnoException} */ (error)).code === 'ENOENT') {
          continue;
        }
        throw error;
      }
    }
    return null;
  }

  /**
   * Asserts that the provided payload satisfies the configuration schema.
   * @param {object} payload
   * @param {string} context
   * @returns {Promise<void>}
   */
  async #assertValid(payload, context) {
    const validator = await this.#getValidator();
    const valid = validator(payload);
    if (!valid) {
      const issues = (validator.errors ?? []).map((error) => this.#formatError(error));
      throw new CodexRcConfigError(`Configuration validation failed for ${context}`, issues);
    }
  }

  /**
   * Compiles the configuration schema.
   * @returns {Promise<Function>}
   */
  async #getValidator() {
    if (this.compiledValidator) {
      return this.compiledValidator;
    }
    const schema = await this.#loadSchema();
    try {
      this.compiledValidator = this.ajv.compile(schema);
    } catch (error) {
      throw new CodexRcConfigError('Unable to compile CodexBridge configuration schema.', [
        error instanceof Error ? error.message : 'Unknown schema compilation error'
      ]);
    }
    return this.compiledValidator;
  }

  /**
   * Reads the JSON schema from disk.
   * @returns {Promise<object>}
   */
  async #loadSchema() {
    if (this.schema) {
      return this.schema;
    }
    const rawSchema = await fs.readFile(this.schemaPath, 'utf-8');
    try {
      this.schema = JSON.parse(rawSchema);
    } catch (error) {
      throw new CodexRcConfigError('Failed to parse CodexBridge configuration schema.', [
        error instanceof Error ? error.message : 'Unknown schema parse error'
      ]);
    }
    return this.schema;
  }

  /**
   * Merges overrides onto the default configuration without mutating inputs.
   * @param {Partial<CodexBridgeConfig>} overrides
   * @returns {CodexBridgeConfig}
   */
  #mergeConfig(overrides) {
    return /** @type {CodexBridgeConfig} */ (this.#mergeDeep(DEFAULT_CODEXBRIDGE_CONFIG, overrides ?? {}));
  }

  /**
   * Deep merge helper that respects plain objects and replaces arrays/primitives.
   * @param {unknown} base
   * @param {unknown} overrides
   * @returns {unknown}
   */
  #mergeDeep(base, overrides) {
    if (Array.isArray(base) || Array.isArray(overrides)) {
      return overrides !== undefined ? this.#clone(overrides) : this.#clone(base);
    }

    if (this.#isPlainObject(base) || this.#isPlainObject(overrides)) {
      const baseObj = this.#isPlainObject(base) ? /** @type {Record<string, unknown>} */ (base) : {};
      const overrideObj = this.#isPlainObject(overrides)
        ? /** @type {Record<string, unknown>} */ (overrides)
        : {};
      const result = {};
      const keys = new Set([...Object.keys(baseObj), ...Object.keys(overrideObj)]);
      for (const key of keys) {
        const baseValue = baseObj[key];
        const overrideValue = overrideObj[key];
        if (overrideValue === undefined) {
          result[key] = this.#clone(baseValue);
        } else {
          result[key] = this.#mergeDeep(baseValue, overrideValue);
        }
      }
      return result;
    }

    return overrides === undefined ? this.#clone(base) : overrides;
  }

  /**
   * Produces a deep clone of supported data structures.
   * @param {unknown} value
   * @returns {unknown}
   */
  #clone(value) {
    if (Array.isArray(value)) {
      return value.map((item) => this.#clone(item));
    }
    if (this.#isPlainObject(value)) {
      const clone = {};
      for (const key of Object.keys(value)) {
        clone[key] = this.#clone(value[key]);
      }
      return clone;
    }
    return value;
  }

  /**
   * Determines whether the provided value is a plain object.
   * @param {unknown} value
   * @returns {value is Record<string, unknown>}
   */
  #isPlainObject(value) {
    return typeof value === 'object' && value !== null && Object.getPrototypeOf(value) === Object.prototype;
  }

  /**
   * Formats Ajv validation errors into human readable strings.
   * @param {import('ajv').ErrorObject} error
   * @returns {string}
   */
  #formatError(error) {
    const dataPath = error.instancePath || error.schemaPath;
    const message = error.message ?? 'Schema validation error.';
    if (error.keyword === 'additionalProperties' && error.params?.additionalProperty) {
      return `${dataPath} Unexpected property: ${error.params.additionalProperty}.`;
    }
    if (error.keyword === 'enum') {
      return `${dataPath} ${message}. Allowed values: ${error.params?.allowedValues?.join(', ')}`;
    }
    return `${dataPath} ${message}`;
  }

  /**
   * Resolves relative configuration paths into absolute equivalents.
   * @param {CodexBridgeConfig} config
   * @returns {LoadedCodexBridgeConfig['resolved']}
   */
  #resolvePaths(config) {
    const resolvePath = (target) => (path.isAbsolute(target) ? target : path.resolve(this.repoRoot, target));
    return {
      repoRoot: this.repoRoot,
      plans: {
        incomingDir: resolvePath(config.plans.incomingDir),
        processedDir: resolvePath(config.plans.processedDir),
        rejectedDir: resolvePath(config.plans.rejectedDir)
      },
      macros: {
        rootDir: resolvePath(config.macros.rootDir),
        registryPath: resolvePath(config.macros.registryPath),
        typesImport: config.macros.typesImport,
        typesSymbol: config.macros.typesSymbol,
        functionSuffix: config.macros.functionSuffix
      },
      cache: {
        macro: resolvePath(config.cache.macro),
        tests: resolvePath(config.cache.tests)
      },
      resultsDir: resolvePath(config.resultsDir),
      tests: {
        defaultCommand: config.tests.defaultCommand,
        defaultTimeoutSeconds: config.tests.defaultTimeoutSeconds
      }
    };
  }
}

/**
 * Convenience helper to load configuration in a single call.
 * @param {CodexRcLoaderOptions} [options]
 * @returns {Promise<LoadedCodexBridgeConfig>}
 */
export async function loadCodexBridgeConfig(options = {}) {
  const loader = new CodexRcLoader(options);
  return loader.load();
}

// ==========================================================================
// Performance Considerations
// ==========================================================================
// - Configuration schema is compiled once and cached for subsequent loads.
// - Directory resolution avoids repeated path joins by memoising repo root.
// - Deep merge utility avoids expensive JSON serialisation for cloning.

// ==========================================================================
// Exports / Public API
// ==========================================================================
export default CodexRcLoader;
