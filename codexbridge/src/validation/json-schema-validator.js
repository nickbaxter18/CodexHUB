/**
 * ==========================================================================
 * Header & Purpose
 * ==========================================================================
 * Module Name: codexbridge/src/validation/json-schema-validator.js
 * Responsibility: Provide a reusable JSON Schema validation helper that
 *                 encapsulates Ajv configuration, schema loading, and
 *                 compilation caching for CodexBridge components.
 * Why it matters: Centralising schema validation guarantees consistent
 *                 behaviour across modules (plan validator, watchers, tests)
 *                 while enabling focused unit tests for schema compliance.
 */

// ==========================================================================
// Imports / Dependencies
// ==========================================================================
import { promises as fs } from "fs";
import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

// ==========================================================================
// Types / Interfaces / Schemas
// ==========================================================================
/** @typedef {import('ajv').default} AjvInstance */
/** @typedef {import('ajv').ErrorObject} AjvError */

/**
 * @typedef {Object} JsonSchemaValidatorOptions
 * @property {string} [schemaPath] - Optional filesystem path to the schema file.
 * @property {object} [schema] - Pre-loaded schema used instead of reading from disk.
 * @property {AjvInstance} [ajv] - Pre-configured Ajv instance for advanced scenarios.
 * @property {ConstructorParameters<typeof Ajv2020>[0]} [ajvOptions] - Additional Ajv options.
 */

/**
 * Shape returned by {@link JsonSchemaValidator#validate}.
 * @typedef {Object} JsonSchemaValidationResult
 * @property {boolean} valid
 * @property {AjvError[]} [errors]
 */

// ==========================================================================
// Error & Edge Handling
// ==========================================================================
export class SchemaValidationError extends Error {
  /**
   * @param {string} message
   * @param {string[]} [issues]
   */
  constructor(message, issues = []) {
    super(message);
    this.name = "SchemaValidationError";
    this.issues = issues;
  }
}

// ==========================================================================
// Core Logic / Implementation
// ==========================================================================
/**
 * Factory helper supplying CodexBridge's default Ajv configuration.
 * @param {ConstructorParameters<typeof Ajv2020>[0]} [overrides]
 * @returns {AjvInstance}
 */
export function createDefaultAjv(overrides = {}) {
  const ajv = new Ajv2020({
    strict: false,
    allErrors: true,
    allowUnionTypes: true,
    coerceTypes: false,
    removeAdditional: false,
    ...overrides,
  });
  addFormats(ajv);
  return ajv;
}

export class JsonSchemaValidator {
  /**
   * @param {JsonSchemaValidatorOptions} [options]
   */
  constructor(options = {}) {
    this.schemaPath = options.schemaPath ?? null;
    this.initialSchema = options.schema ?? null;
    this.schema = options.schema ?? null;
    this.ajv = options.ajv ?? createDefaultAjv(options.ajvOptions);
    this.compiledValidator = null;
  }

  /**
   * Loads the schema either from memory or disk exactly once.
   * @returns {Promise<object>}
   */
  async loadSchema() {
    if (this.schema) {
      return this.schema;
    }
    if (!this.schemaPath) {
      throw new SchemaValidationError(
        "Schema path must be provided when no schema object is supplied."
      );
    }

    const buffer = await fs.readFile(this.schemaPath, "utf-8");
    try {
      this.schema = JSON.parse(buffer);
    } catch (error) {
      const detail =
        error instanceof Error ? error.message : "Unknown schema parse error";
      throw new SchemaValidationError(
        "Failed to parse schema JSON from disk.",
        [detail]
      );
    }
    return this.schema;
  }

  /**
   * Compiles the schema using Ajv and caches the validator function.
   * @returns {Promise<Function>}
   */
  async #getValidator() {
    if (this.compiledValidator) {
      return this.compiledValidator;
    }

    const schema = await this.loadSchema();
    try {
      this.compiledValidator = this.ajv.compile(schema);
    } catch (error) {
      const detail =
        error instanceof Error
          ? error.message
          : "Unknown schema compilation error";
      throw new SchemaValidationError("Unable to compile schema.", [detail]);
    }
    return this.compiledValidator;
  }

  /**
   * Validates arbitrary payloads against the compiled schema.
   * @param {unknown} payload
   * @returns {Promise<JsonSchemaValidationResult>}
   */
  async validate(payload) {
    const validator = await this.#getValidator();
    const valid = validator(payload);
    if (valid) {
      return { valid: true };
    }
    return { valid: false, errors: validator.errors ?? [] };
  }

  /**
   * Clears cached schema and compiled validator, useful for hot-reload scenarios.
   */
  reset() {
    this.schema = this.initialSchema;
    this.compiledValidator = null;
  }
}

// ==========================================================================
// Performance Considerations
// ==========================================================================
// - Validators are compiled once per schema instance which minimises repeated
//   Ajv compilation costs across watcher runs.
// - Consumers can inject pre-built Ajv instances with memoised formats for
//   advanced performance tuning.

// ==========================================================================
// Exports / Public API
// ==========================================================================
export default JsonSchemaValidator;
