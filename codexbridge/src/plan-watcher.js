/**
 * ==========================================================================
 * Header & Purpose
 * ==========================================================================
 * Module Name: codexbridge/src/plan-watcher.js
 * Responsibility: Process CodexBridge plan inboxes, enforce governance rules,
 *                 scaffold macro stubs, update registries/caches, and trigger
 *                 verification workflows so automation remains auditable.
 * Why it matters: Without a watcher, validated plans never materialise into
 *                 executable artefacts. This module operationalises planning
 *                 output into traceable macros while preserving safety gates.
 */

// ==========================================================================
// Imports / Dependencies
// ==========================================================================
import { promises as fs } from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { exec } from "child_process";
import { promisify } from "util";
import crypto from "crypto";

import PlanValidator, { PlanValidationError } from "./plan-validator.js";

// ==========================================================================
// Types / Interfaces / Schemas (JSDoc for tooling clarity)
// ==========================================================================
/**
 * @typedef {import('./plan-validator.js').CodexBridgePlan} CodexBridgePlan
 */

/**
 * @typedef {Object} PlanWatcherOptions
 * @property {string} [repoRoot] - Repository root. Defaults to `process.cwd()`.
 * @property {string} [plansDir] - Directory containing incoming plans.
 * @property {string} [processedDir] - Directory for successfully processed plans.
 * @property {string} [rejectedDir] - Directory for rejected plans.
 * @property {string} [macrosDir] - Directory where macro files are generated.
 * @property {string} [registryPath] - Path to `macros/registry.json`.
 * @property {string} [macroTypesImport] - Override import specifier for macro context types.
 * @property {string} [macroTypesSymbol] - Symbol imported for macro context typing.
 * @property {string} [macroSuffix] - Suffix appended to generated function names.
 * @property {string} [defaultTestCommand] - Command executed when plans omit tests.
 * @property {number} [defaultTestTimeout] - Timeout (seconds) when plans omit timeouts.
 * @property {PlanValidator} [validator] - Preconfigured plan validator instance.
 * @property {(command: string, options?: import('child_process').ExecOptions) => Promise<{stdout: string, stderr: string}>} [runCommand]
 *   - Strategy for executing shell commands, defaults to `exec`.
 * @property {Console} [logger] - Logger used for informational messages.
 * @property {string} [resultsDir] - Directory capturing plan execution results.
 * @property {string} [macroCachePath] - JSON cache recording macro generation metadata.
 * @property {string} [testCachePath] - JSON cache capturing test outcomes.
 */

/**
 * @typedef {Object} PlanProcessingOutcome
 * @property {'processed'|'rejected'} status
 * @property {string} filename
 * @property {string} [reason]
 * @property {string} [macroPath]
 */

// ==========================================================================
// Error & Edge Handling Utilities
// ==========================================================================
/**
 * Error thrown when a plan fails during processing after validation.
 */
export class PlanProcessingError extends Error {
  /**
   * @param {string} message - Description of the processing failure.
   * @param {object} [details] - Additional metadata for debugging.
   */
  constructor(message, details = {}) {
    super(message);
    this.name = "PlanProcessingError";
    this.details = details;
  }
}

/**
 * Default command runner using child_process.exec wrapped in a promise.
 * @param {string} command
 * @param {import('child_process').ExecOptions} [options]
 * @returns {Promise<{stdout: string, stderr: string}>}
 */
const defaultCommandRunner = async (command, options = {}) => {
  const execAsync = promisify(exec);
  return execAsync(command, options);
};

// ==========================================================================
// Core Logic / Implementation
// ==========================================================================
export class PlanWatcher {
  /**
   * @param {PlanWatcherOptions} [options]
   */
  constructor(options = {}) {
    const repoRoot = options.repoRoot ?? process.cwd();

    this.repoRoot = repoRoot;
    this.validator = options.validator ?? new PlanValidator();
    this.logger = options.logger ?? console;

    this.plansDir =
      options.plansDir ?? path.join(repoRoot, "plans", "from_gpt");
    this.processedDir =
      options.processedDir ?? path.join(repoRoot, "plans", "processed");
    this.rejectedDir =
      options.rejectedDir ?? path.join(repoRoot, "plans", "rejected");
    this.macrosDir = options.macrosDir ?? path.join(repoRoot, "macros");
    this.registryPath =
      options.registryPath ?? path.join(this.macrosDir, "registry.json");
    this.resultsDir = options.resultsDir ?? path.join(repoRoot, "results");
    this.macroCachePath =
      options.macroCachePath ??
      path.join(repoRoot, "cache", "macro_output.json");
    this.testCachePath =
      options.testCachePath ??
      path.join(repoRoot, "cache", "test_outcomes.json");

    this.macroTypesImport = options.macroTypesImport ?? null;
    this.macroTypesSymbol = options.macroTypesSymbol ?? "MacroContext";
    this.macroSuffix = options.macroSuffix ?? "Macro";

    this.defaultTestCommand = options.defaultTestCommand ?? "npm test";
    this.defaultTestTimeout = options.defaultTestTimeout ?? 600; // seconds

    this.runCommand = options.runCommand ?? defaultCommandRunner;
  }

  /**
   * Processes every JSON file in the plan inbox sequentially.
   * @returns {Promise<PlanProcessingOutcome[]>}
   */
  async processPendingPlans() {
    await this.#ensureDirectories();
    const entries = await this.#listPlanFiles();

    const outcomes = [];
    for (const file of entries) {
      const absolutePath = path.join(this.plansDir, file);
      const outcome = await this.#handlePlanFile(absolutePath);
      outcomes.push(outcome);
    }
    return outcomes;
  }

  /**
   * Lists plan files sorted lexicographically for deterministic processing.
   * @returns {Promise<string[]>}
   */
  async #listPlanFiles() {
    try {
      const items = await fs.readdir(this.plansDir);
      return items.filter((item) => item.endsWith(".json")).sort();
    } catch (error) {
      if (/** @type {NodeJS.ErrnoException} */ (error).code === "ENOENT") {
        return [];
      }
      throw error;
    }
  }

  /**
   * Ensures required directories exist to avoid race conditions during writes.
   * @returns {Promise<void>}
   */
  async #ensureDirectories() {
    const directories = [
      this.plansDir,
      this.processedDir,
      this.rejectedDir,
      this.macrosDir,
      path.dirname(this.registryPath),
      path.dirname(this.macroCachePath),
      path.dirname(this.testCachePath),
      this.resultsDir,
    ];
    await Promise.all(
      directories.map((dir) => fs.mkdir(dir, { recursive: true }))
    );
  }

  /**
   * Handles a single plan file end-to-end.
   * @param {string} filePath
   * @returns {Promise<PlanProcessingOutcome>}
   */
  async #handlePlanFile(filePath) {
    const filename = path.basename(filePath);
    const rawContent = await fs.readFile(filePath, "utf-8");
    let parsedPlan;

    try {
      parsedPlan = JSON.parse(rawContent);
    } catch (error) {
      const reason = "Invalid JSON payload supplied by planner.";
      await this.#archiveRejected({
        filename,
        originalPath: filePath,
        rawContent,
        rejectionReason: reason,
        issues: [
          error instanceof Error ? error.message : "Unknown JSON parse error",
        ],
      });
      await this.#writeResultArtifact({
        filename,
        status: "rejected",
        failureReason: reason,
        failureDetails: {
          issues: [
            error instanceof Error ? error.message : "Unknown JSON parse error",
          ],
        },
      });
      return { status: "rejected", filename, reason };
    }

    try {
      await this.validator.assertValid(parsedPlan, filename);
    } catch (error) {
      const issues =
        error instanceof PlanValidationError
          ? (error.issues ?? [])
          : [
              error instanceof Error
                ? error.message
                : "Unknown validation error",
            ];
      const reason = "Plan failed schema validation.";
      await this.#archiveRejected({
        filename,
        originalPath: filePath,
        plan: parsedPlan,
        rawContent,
        rejectionReason: reason,
        issues,
      });
      await this.#writeResultArtifact({
        filename,
        plan: parsedPlan,
        status: "rejected",
        failureReason: reason,
        failureDetails: { issues },
      });
      return { status: "rejected", filename, reason };
    }

    const plan = /** @type {CodexBridgePlan} */ (parsedPlan);
    const gate = this.validator.getAutomationGate(plan);
    if (!gate.autoExecutable) {
      const reason = gate.reason ?? "Automation disabled by policy flags.";
      await this.#archiveRejected({
        filename,
        originalPath: filePath,
        plan,
        rawContent,
        rejectionReason: reason,
        issues: gate.reason ? [gate.reason] : [],
      });
      await this.#writeResultArtifact({
        filename,
        plan,
        status: "rejected",
        failureReason: reason,
        failureDetails: gate.reason ? { issues: [gate.reason] } : undefined,
      });
      return { status: "rejected", filename, reason };
    }

    const missingDependencies = await this.#findMissingDependencies(plan);
    if (missingDependencies.length > 0) {
      const reason = `Missing dependencies: ${missingDependencies.join(", ")}`;
      await this.#archiveRejected({
        filename,
        originalPath: filePath,
        plan,
        rawContent,
        rejectionReason: reason,
        issues: [
          "All dependencies must exist in macros/registry.json before execution.",
        ],
      });
      await this.#writeResultArtifact({
        filename,
        plan,
        status: "rejected",
        failureReason: reason,
        failureDetails: {
          issues: [
            "All dependencies must exist in macros/registry.json before execution.",
          ],
        },
      });
      return { status: "rejected", filename, reason };
    }

    const macroExists = await this.#macroAlreadyRegistered(plan.macro);
    if (macroExists) {
      const reason = `Macro ${plan.macro} already registered.`;
      await this.#archiveRejected({
        filename,
        originalPath: filePath,
        plan,
        rawContent,
        rejectionReason: reason,
        issues: ["Duplicate macros must be handled manually."],
      });
      await this.#writeResultArtifact({
        filename,
        plan,
        status: "rejected",
        failureReason: reason,
        failureDetails: {
          issues: ["Duplicate macros must be handled manually."],
        },
      });
      return { status: "rejected", filename, reason };
    }

    const registryBefore = await this.#readJsonFile(this.registryPath, {
      version: 1,
      macros: [],
    });

    try {
      const macroPath = await this.#generateMacroStub(plan, filename);
      const registryEntry = await this.#updateRegistry(plan, macroPath);
      let testResults;
      try {
        testResults = await this.#executePlanTests(plan);
      } catch (error) {
        await fs.rm(macroPath, { force: true });
        await this.#writeJsonFile(this.registryPath, registryBefore);
        throw error;
      }

      await this.#updateMacroCache(plan, macroPath);
      await this.#updateTestCache(plan, testResults);
      await this.#writeResultArtifact({
        filename,
        plan,
        macroPath,
        testResults,
        status: "processed",
      });
      await this.#archiveProcessed({
        filename,
        originalPath: filePath,
        plan,
        rawContent,
        macroPath,
        registryEntry,
        testResults,
      });
      this.logger.info?.(`Processed plan ${filename} → ${macroPath}`);
      return { status: "processed", filename, macroPath };
    } catch (error) {
      const reason =
        error instanceof PlanProcessingError
          ? error.message
          : error instanceof Error
            ? error.message
            : "Unknown plan processing failure.";
      await this.#writeResultArtifact({
        filename,
        plan,
        status: "rejected",
        failureReason: reason,
        failureDetails:
          error instanceof PlanProcessingError
            ? error.details
            : error instanceof PlanValidationError
              ? { issues: error.issues }
              : undefined,
      });
      await this.#archiveRejected({
        filename,
        originalPath: filePath,
        plan,
        rawContent,
        rejectionReason: reason,
        issues:
          error instanceof PlanProcessingError && error.details?.issues
            ? error.details.issues
            : [],
      });
      return { status: "rejected", filename, reason };
    }
  }

  /**
   * Determines which dependencies are missing from the registry.
   * @param {CodexBridgePlan} plan
   * @returns {Promise<string[]>}
   */
  async #findMissingDependencies(plan) {
    if (!plan.dependencies || plan.dependencies.length === 0) {
      return [];
    }
    const registry = await this.#readJsonFile(this.registryPath, {
      version: 1,
      macros: [],
    });
    const registered = new Set(
      registry.macros?.map((macro) => macro.identifier) ?? []
    );
    return plan.dependencies.filter(
      (dependency) => !registered.has(dependency)
    );
  }

  /**
   * Checks whether a macro already exists in the registry.
   * @param {string} identifier
   * @returns {Promise<boolean>}
   */
  async #macroAlreadyRegistered(identifier) {
    const registry = await this.#readJsonFile(this.registryPath, {
      version: 1,
      macros: [],
    });
    return (registry.macros ?? []).some(
      (macro) => macro.identifier === identifier
    );
  }

  /**
   * Generates a macro stub file containing descriptive boilerplate.
   * @param {CodexBridgePlan} plan
   * @param {string} filename - Source plan filename for attribution.
   * @returns {Promise<string>} - Absolute path to the generated macro file.
   */
  async #generateMacroStub(plan, filename) {
    const segments = this.#macroIdentifierToSegments(plan.macro);
    const macroDir = path.join(this.macrosDir, ...segments.slice(0, -1));
    await fs.mkdir(macroDir, { recursive: true });
    const fileName = `${segments[segments.length - 1]}.ts`;
    const macroPath = path.join(macroDir, fileName);

    const functionName = this.#macroIdentifierToFunctionName(plan.macro);
    const generatedAt = new Date().toISOString();
    const relativeTypes = path
      .relative(macroDir, path.join(this.macrosDir, "types.ts"))
      .replace(/\\/g, "/");
    const importPath =
      this.macroTypesImport ??
      this.#normaliseImportPath(relativeTypes.replace(/\.ts$/, ""));
    const paramDocs = plan.inputs
      .map(
        (input) =>
          ` * @param {${input.type}} ${input.name} - ${input.description ?? "Macro input."}`
      )
      .join("\n");
    const headerComment = `/**\n * Auto-generated macro stub.\n * Macro Identifier: ${plan.macro}\n * Description: ${plan.description}\n * Domain: ${plan.domain}\n * Source Plan: ${filename}\n * Generated: ${generatedAt}\n${paramDocs ? "\n *\n" + paramDocs : ""}\n */`;

    const content = `${headerComment}

import type { ${this.macroTypesSymbol} } from '${importPath}';

export async function ${functionName}(context: ${this.macroTypesSymbol}): Promise<unknown> {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const executionContext = context;
  // Placeholder: Macro logic must be supplied by a human reviewer to satisfy governance.
  throw new Error('Macro ${plan.macro} is not implemented yet.');
}

export default ${functionName};
`;

    await fs.writeFile(macroPath, content, "utf-8");
    return macroPath;
  }

  /**
   * Normalises relative import paths so generated TypeScript remains portable.
   * @param {string} importPath
   * @returns {string}
   */
  #normaliseImportPath(importPath) {
    if (importPath.startsWith(".")) {
      return importPath;
    }
    return `./${importPath}`;
  }

  /**
   * Converts a macro identifier (e.g. ::frontend.dashboard) into path-safe segments.
   * @param {string} identifier
   * @returns {string[]}
   */
  #macroIdentifierToSegments(identifier) {
    const trimmed = identifier.replace(/^::/, "");
    const rawSegments = trimmed.split(/[.:]/).filter(Boolean);
    if (rawSegments.length === 0) {
      throw new PlanProcessingError(
        "Unable to derive macro filename from identifier.",
        {
          issues: [
            "Macro identifier must include at least one alphanumeric segment.",
          ],
        }
      );
    }
    return rawSegments.map((segment) =>
      segment.replace(/[^a-zA-Z0-9_-]/g, "-").toLowerCase()
    );
  }

  /**
   * Creates a PascalCase function name from a macro identifier.
   * @param {string} identifier
   * @returns {string}
   */
  #macroIdentifierToFunctionName(identifier) {
    const segments = this.#macroIdentifierToSegments(identifier);
    const capitalised = segments.map((segment) =>
      segment
        .split(/[-_]/)
        .filter(Boolean)
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join("")
    );
    return `${capitalised.join("")}${this.macroSuffix}`;
  }

  /**
   * Updates macros/registry.json with new macro metadata.
   * @param {CodexBridgePlan} plan
   * @param {string} macroPath
   * @returns {Promise<object>} - Registry entry written to disk.
   */
  async #updateRegistry(plan, macroPath) {
    const registry = await this.#readJsonFile(this.registryPath, {
      version: 1,
      macros: [],
    });
    const entry = {
      identifier: plan.macro,
      description: plan.description,
      domain: plan.domain,
      safe: plan.safe,
      requires_review: plan.requires_review,
      inputs: plan.inputs,
      dependencies: plan.dependencies ?? [],
      version: plan.version ?? "0.1.0",
      macro_path: path.relative(this.repoRoot, macroPath),
      generated_at: new Date().toISOString(),
    };

    const macros = [...(registry.macros ?? []), entry];
    macros.sort((a, b) => a.identifier.localeCompare(b.identifier));
    const nextRegistry = { ...registry, macros };
    await this.#writeJsonFile(this.registryPath, nextRegistry);
    return entry;
  }

  /**
   * Executes test commands declared by the plan or falls back to default tests.
   * @param {CodexBridgePlan} plan
   * @returns {Promise<object[]>}
   */
  async #executePlanTests(plan) {
    const tests =
      plan.tests && plan.tests.length > 0 ? plan.tests : [{ type: "default" }];
    const results = [];
    for (const test of tests) {
      const command = test.command ?? this.defaultTestCommand;
      const timeout = (test.timeout ?? this.defaultTestTimeout) * 1000;
      const env = { ...process.env, ...(test.env ?? {}) };
      const start = Date.now();
      try {
        const { stdout, stderr } = await this.runCommand(command, {
          cwd: this.repoRoot,
          env,
          timeout,
        });
        const durationMs = Date.now() - start;
        results.push({
          status: "passed",
          type: test.type ?? "custom",
          command,
          stdout,
          stderr,
          durationMs,
        });
      } catch (error) {
        const durationMs = Date.now() - start;
        const stdout = error?.stdout ?? "";
        const stderr =
          error?.stderr ?? (error instanceof Error ? error.message : "");
        throw new PlanProcessingError("Plan tests failed.", {
          issues: [stderr || "Test command exited with non-zero status."],
          command,
          durationMs,
          stdout,
          stderr,
        });
      }
    }
    return results;
  }

  /**
   * Persists macro generation metadata into cache/macro_output.json.
   * @param {CodexBridgePlan} plan
   * @param {string} macroPath
   * @returns {Promise<void>}
   */
  async #updateMacroCache(plan, macroPath) {
    const cache = await this.#readJsonFile(this.macroCachePath, { macros: {} });
    const macros = cache.macros ?? {};
    macros[plan.macro] = {
      macro_path: path.relative(this.repoRoot, macroPath),
      generated_at: new Date().toISOString(),
      status: "stub_created",
    };
    await this.#writeJsonFile(this.macroCachePath, { ...cache, macros });
  }

  /**
   * Persists test results metadata into cache/test_outcomes.json.
   * @param {CodexBridgePlan} plan
   * @param {object[]} testResults
   * @returns {Promise<void>}
   */
  async #updateTestCache(plan, testResults) {
    const cache = await this.#readJsonFile(this.testCachePath, { macros: {} });
    const macros = cache.macros ?? {};
    macros[plan.macro] = {
      last_run: new Date().toISOString(),
      results: testResults,
    };
    await this.#writeJsonFile(this.testCachePath, { ...cache, macros });
  }

  /**
   * Writes summary artefacts to the results directory for planner feedback.
   * @param {object} payload
   * @param {string} payload.filename
   * @param {CodexBridgePlan} [payload.plan]
   * @param {string} [payload.macroPath]
   * @param {object[]} [payload.testResults]
   * @param {'processed'|'rejected'} payload.status
   * @param {string} [payload.failureReason]
   * @param {object} [payload.failureDetails]
   * @returns {Promise<void>}
   */
  async #writeResultArtifact(payload) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    const baseName = payload.filename.replace(/\.json$/, "");
    const targetPath = path.join(
      this.resultsDir,
      `${timestamp}__${baseName}__${payload.status}.json`
    );
    const serialisable = {
      plan_identifier: payload.plan?.macro,
      status: payload.status,
      macro_path: payload.macroPath
        ? path.relative(this.repoRoot, payload.macroPath)
        : undefined,
      test_results: payload.testResults,
      failure_reason: payload.failureReason,
      failure_details: payload.failureDetails,
    };
    await this.#writeJsonFile(targetPath, serialisable);
  }

  /**
   * Archives a successfully processed plan into the processed directory.
   * @param {object} options
   * @param {string} options.filename
   * @param {string} options.originalPath
   * @param {CodexBridgePlan} options.plan
   * @param {string} options.rawContent
   * @param {string} options.macroPath
   * @param {object} options.registryEntry
   * @param {object[]} options.testResults
   * @returns {Promise<void>}
   */
  async #archiveProcessed(options) {
    const payload = {
      ...options.plan,
      codexbridge: {
        status: "processed",
        processed_at: new Date().toISOString(),
        macro_path: path.relative(this.repoRoot, options.macroPath),
        registry_entry: options.registryEntry,
        tests: options.testResults,
        plan_sha256: this.#hashContent(options.rawContent),
      },
    };
    const targetPath = path.join(this.processedDir, options.filename);
    await this.#writeJsonFile(targetPath, payload);
    await fs.rm(options.originalPath, { force: true });
  }

  /**
   * Archives rejected plans with diagnostics for manual review.
   * @param {object} options
   * @param {string} options.filename
   * @param {string} options.originalPath
   * @param {CodexBridgePlan} [options.plan]
   * @param {string} [options.rawContent]
   * @param {string} options.rejectionReason
   * @param {string[]} [options.issues]
   * @returns {Promise<void>}
   */
  async #archiveRejected(options) {
    const payload = {
      ...(options.plan ?? {}),
      codexbridge: {
        status: "rejected",
        processed_at: new Date().toISOString(),
        reason: options.rejectionReason,
        issues: options.issues ?? [],
        plan_sha256: options.rawContent
          ? this.#hashContent(options.rawContent)
          : undefined,
      },
    };
    if (!options.plan && options.rawContent) {
      payload.raw_plan = options.rawContent;
    }
    const targetPath = path.join(this.rejectedDir, options.filename);
    await this.#writeJsonFile(targetPath, payload);
    await fs.rm(options.originalPath, { force: true });
  }

  /**
   * Reads JSON content from disk and returns a fallback value on ENOENT.
   * @template T
   * @param {string} filePath
   * @param {T} fallback
   * @returns {Promise<T>}
   */
  async #readJsonFile(filePath, fallback) {
    try {
      const content = await fs.readFile(filePath, "utf-8");
      return JSON.parse(content);
    } catch (error) {
      if (/** @type {NodeJS.ErrnoException} */ (error).code === "ENOENT") {
        return fallback;
      }
      throw error;
    }
  }

  /**
   * Serialises an object to JSON on disk with stable formatting.
   * @param {string} filePath
   * @param {unknown} data
   * @returns {Promise<void>}
   */
  async #writeJsonFile(filePath, data) {
    await fs.mkdir(path.dirname(filePath), { recursive: true });
    const json = JSON.stringify(data, null, 2);
    await fs.writeFile(filePath, json, "utf-8");
  }

  /**
   * Computes a SHA-256 hash of provided content.
   * @param {string} content
   * @returns {string}
   */
  #hashContent(content) {
    return crypto.createHash("sha256").update(content).digest("hex");
  }
}

// ==========================================================================
// Performance Considerations
// ==========================================================================
// - Plans are processed sequentially to maintain deterministic registry updates
//   and avoid race conditions when generating files.
// - File system operations rely on async APIs, keeping the event loop unblocked.
// - Registry content is read and written only when necessary, reducing I/O.

// ==========================================================================
// Exports / Public API
// ==========================================================================
export default PlanWatcher;

const modulePath = fileURLToPath(import.meta.url);
if (process.argv[1] && path.resolve(process.argv[1]) === modulePath) {
  // Module executed via `node codexbridge/src/plan-watcher.js`
  const watcher = new PlanWatcher();
  watcher
    .processPendingPlans()
    .then((outcomes) => {
      const summary = outcomes
        .map((outcome) => `${outcome.filename}:${outcome.status}`)
        .join(", ");
      console.log(
        `CodexBridge watcher processed plans → ${summary || "no pending plans."}`
      );
    })
    .catch((error) => {
      console.error("CodexBridge watcher encountered an error:", error);
      process.exitCode = 1;
    });
}
