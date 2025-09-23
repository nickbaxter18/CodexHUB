/**
 * ==========================================================================
 * Header & Purpose
 * ==========================================================================
 * Module Name: codexbridge/src/plan-validator.js
 * Responsibility: Runtime validator enforcing the CodexBridge plan schema and
 *                 automation safety rules prior to macro generation.
 * Why it matters: Plans originate from a remote GPT planner and are therefore
 *                 untrusted input. Rigorous validation prevents malformed or
 *                 unsafe plans from executing inside the developer workstation.
 */

// ==========================================================================
// Imports / Dependencies
// ==========================================================================
import { promises as fs } from 'fs';
import path from 'path';
import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';

// ==========================================================================
// Types / Interfaces / Schemas (JSDoc based for strong tooling support)
// ==========================================================================
/**
 * @typedef {Object} PlanInput
 * @property {string} name - Macro argument identifier exposed to TypeScript callers.
 * @property {string} type - Type descriptor that the generated macro must honour.
 * @property {string} [description] - Human friendly explanation of the argument.
 * @property {boolean} [required=true] - Flag indicating if the argument must be supplied.
 * @property {*} [default] - Default value used when the planner supplies optional inputs.
 * @property {*} [example] - Example illustrating expected values for QA review.
 */

/**
 * @typedef {Object} PlanTest
 * @property {('unit'|'integration'|'schema'|'lint'|'custom')} type - Classification of the test.
 * @property {string} [command] - Command executed by the watcher for the test.
 * @property {string} [path] - Optional file path to scope execution.
 * @property {string} [description] - Human readable description of the test intent.
 * @property {number} [timeout] - Timeout in seconds enforced by the watcher.
 * @property {Record<string,string>} [env] - Environment variables injected before execution.
 */

/**
 * @typedef {Object} PlanGovernance
 * @property {string[]} [policy_refs] - Policies cited by the planner.
 * @property {string} [escalation_path] - Escalation steps for human reviewers.
 * @property {string} [manual_review_reason] - Reason a plan requires manual approval.
 */

/**
 * @typedef {Object} CodexBridgePlan
 * @property {string} macro - Identifier for the macro to generate.
 * @property {string} description - Human readable description of the macro.
 * @property {string} domain - Functional domain for routing and policy enforcement.
 * @property {PlanInput[]} inputs - Collection of macro arguments.
 * @property {boolean} safe - Whether the macro can run automatically.
 * @property {boolean} requires_review - Whether a human must approve execution.
 * @property {string} [created_at] - ISO timestamp describing when GPT produced the plan.
 * @property {string} [version] - Semantic version assigned by the planner.
 * @property {PlanTest[]} [tests] - Optional tests to execute post generation.
 * @property {string[]} [dependencies] - Other macros that must exist first.
 * @property {PlanGovernance} [governance] - Policy metadata for auditing.
 * @property {string} [notes] - Additional context for humans.
 */

/**
 * Shape describing the result of a validation attempt.
 * @typedef {Object} ValidationResult
 * @property {boolean} valid - Indicates whether the plan satisfied the schema.
 * @property {string[]} [errors] - Human readable error messages when validation fails.
 */

/**
 * Options accepted by the {@link PlanValidator} constructor.
 * @typedef {Object} PlanValidatorOptions
 * @property {string} [schemaPath] - Optional override for the schema location.
 * @property {import('ajv').default} [ajv] - Pre-configured Ajv instance (mainly for testing).
 */

// ==========================================================================
// Error & Edge Handling Utilities
// ==========================================================================
/**
 * Custom error providing structured validation diagnostics.
 */
export class PlanValidationError extends Error {
  /**
   * @param {string} message - Human readable summary of validation failures.
   * @param {string[]} [issues] - Detailed validation problems for auditing.
   */
  constructor(message, issues = []) {
    super(message);
    this.name = 'PlanValidationError';
    this.issues = issues;
  }
}

// ==========================================================================
// Core Logic / Implementation
// ==========================================================================
export class PlanValidator {
  /**
   * @param {PlanValidatorOptions} [options]
   */
  constructor(options = {}) {
    const defaultSchemaPath = path.join(
      process.cwd(),
      'codexbridge',
      'schemas',
      'plan.schema.json'
    );
    this.schemaPath = options.schemaPath ?? defaultSchemaPath;
    this.ajv = options.ajv ?? this.#createAjvInstance();
    this.compiledValidator = null;
    this.schema = null;
  }

  /**
   * Lazily initialises an Ajv instance with the formats used in the schema.
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
   * Loads the JSON schema from disk exactly once.
   * @returns {Promise<object>}
   */
  async loadSchema() {
    if (this.schema) {
      return this.schema;
    }

    const schemaBuffer = await fs.readFile(this.schemaPath, 'utf-8');
    try {
      this.schema = JSON.parse(schemaBuffer);
    } catch (error) {
      throw new PlanValidationError('Failed to parse plan schema JSON.', [
        error instanceof Error ? error.message : 'Unknown schema parse error'
      ]);
    }
    return this.schema;
  }

  /**
   * Compiles and caches the schema validation function.
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
      throw new PlanValidationError('Unable to compile plan schema.', [
        error instanceof Error ? error.message : 'Unknown schema compilation error'
      ]);
    }
    return this.compiledValidator;
  }

  /**
   * Validates a plan object and returns structured diagnostics.
   * @param {unknown} plan
   * @returns {Promise<ValidationResult>}
   */
  async validate(plan) {
    const validator = await this.#getValidator();
    const valid = validator(plan);

    if (valid) {
      return { valid: true };
    }

    const issues = (validator.errors ?? []).map((error) => this.#formatError(error));
    return { valid: false, errors: issues };
  }

  /**
   * Validates a plan and throws a {@link PlanValidationError} when invalid.
   * @param {unknown} plan
   * @param {string} [context] - Contextual label used in error messages (e.g. filename).
   * @returns {Promise<void>}
   */
  async assertValid(plan, context = 'plan') {
    const result = await this.validate(plan);
    if (!result.valid) {
      const prefix = `Plan validation failed for ${context}`;
      throw new PlanValidationError(prefix, result.errors ?? []);
    }
  }

  /**
   * Reads a JSON plan file, validates the content, and returns the parsed object.
   * @param {string} filePath
   * @returns {Promise<CodexBridgePlan>}
   */
  async validateFile(filePath) {
    const rawContent = await fs.readFile(filePath, 'utf-8');
    let payload;
    try {
      payload = JSON.parse(rawContent);
    } catch (error) {
      throw new PlanValidationError(`Unable to parse JSON plan: ${filePath}`, [
        error instanceof Error ? error.message : 'Unknown parse error'
      ]);
    }

    await this.assertValid(payload, filePath);
    return /** @type {CodexBridgePlan} */ (payload);
  }

  /**
   * Determines whether a plan can run automatically based on safety flags.
   * @param {CodexBridgePlan} plan
   * @returns {{autoExecutable: boolean, reason?: string}}
   */
  getAutomationGate(plan) {
    if (!plan.safe) {
      return {
        autoExecutable: false,
        reason: 'Plan marked as unsafe by planner.'
      };
    }

    if (plan.requires_review) {
      return {
        autoExecutable: false,
        reason: 'Plan requires manual review before execution.'
      };
    }

    return { autoExecutable: true };
  }

  /**
   * Formats Ajv error objects into human readable messages.
   * @param {import('ajv').ErrorObject} error
   * @returns {string}
   */
  #formatError(error) {
    const dataPath = error.instancePath || error.schemaPath;
    const message = error.message ?? 'Schema violation detected.';
    if (error.keyword === 'additionalProperties' && error.params?.additionalProperty) {
      return `${dataPath} Unexpected property: ${error.params.additionalProperty}.`;
    }
    if (error.keyword === 'enum') {
      return `${dataPath} ${message}. Allowed values: ${error.params?.allowedValues?.join(', ')}`;
    }
    return `${dataPath} ${message}`;
  }
}

// ==========================================================================
// Performance Considerations
// ==========================================================================
// - The Ajv validator is compiled once and cached, reducing validation latency
//   when multiple plans are processed sequentially by the watcher.
// - Schema loading is memoised to avoid redundant disk I/O.
// - No synchronous filesystem calls are used, keeping the event loop responsive.

// ==========================================================================
// Exports / Public API
// ==========================================================================
export default PlanValidator;
