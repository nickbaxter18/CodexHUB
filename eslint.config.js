/**
 * ==========================================================================
 * Header & Purpose
 * ==========================================================================
 * File Name: eslint.config.js
 * Responsibility: Bridge the legacy `.eslintrc.json` configuration into
 *                 ESLint's flat config format so modern tooling (CI, editors)
 *                 can execute linting with TypeScript and Prettier support.
 * Why it matters: ESLint 9 requires flat config files. This adapter keeps the
 *                 existing configuration canonical while exposing it to the
 *                 newer loader.
 */

// ==========================================================================
// Imports / Dependencies
// ==========================================================================
import { FlatCompat } from "@eslint/eslintrc";
import js from "@eslint/js";
import { fileURLToPath } from "url";
import path from "path";
import fs from "fs";

// ==========================================================================
// Core Logic / Implementation
// ==========================================================================
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
  recommendedConfig: js.configs.recommended,
  allConfig: js.configs.all,
});

const legacyConfigPath = path.join(__dirname, ".eslintrc.json");
const legacyConfig = JSON.parse(fs.readFileSync(legacyConfigPath, "utf-8"));

export default [...compat.config(legacyConfig)];

// ==========================================================================
// Performance Considerations
// ==========================================================================
// - The legacy configuration is parsed once at startup and reused by ESLint.
// - FlatCompat avoids recomputing plugin resolution during repeated lint runs.

// ==========================================================================
// Exports / Public API
// ==========================================================================
// - Default export consumed by `eslint .` in package scripts.
