/**
 * Macro registry integrity tests keep macros/registry.json aligned with disk state.
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { promises as fs } from "fs";
import path from "path";
import crypto from "crypto";

const REPO_ROOT = process.cwd();
const MACROS_DIR = path.join(REPO_ROOT, "macros");
const REGISTRY_PATH = path.join(MACROS_DIR, "registry.json");

const toPosix = (filePath) => filePath.split(path.sep).join("/");

async function collectMacroFiles(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    if (entry.name.startsWith(".")) {
      continue;
    }
    const entryPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await collectMacroFiles(entryPath)));
    } else if (entry.isFile() && entry.name.endsWith(".ts")) {
      files.push(entryPath);
    }
  }
  return files;
}

async function readRegistry() {
  try {
    const content = await fs.readFile(REGISTRY_PATH, "utf-8");
    return JSON.parse(content);
  } catch (error) {
    if (error.code === "ENOENT") {
      return { version: 1, macros: [] };
    }
    throw error;
  }
}

async function fileExists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

describe("macro registry integrity", () => {
  it("ensures registry entries mirror macro files on disk", async () => {
    const registry = await readRegistry();
    assert.ok(
      Array.isArray(registry.macros),
      "registry.macros must be an array"
    );

    const macroFiles = (await collectMacroFiles(MACROS_DIR)).filter(
      (filePath) => {
        const relative = path.relative(MACROS_DIR, filePath);
        return toPosix(relative) !== "types.ts";
      }
    );

    const entriesByIdentifier = new Map(
      (registry.macros ?? []).map((entry) => [entry.identifier, entry])
    );

    for (const filePath of macroFiles) {
      const relative = path.relative(MACROS_DIR, filePath);
      const relativePosix = toPosix(relative);
      const identifierPath = relativePosix.replace(/\.ts$/, "");
      const identifier = `::${identifierPath.replace(/\//g, ".")}`;
      const entry = entriesByIdentifier.get(identifier);
      assert.ok(entry, `Registry missing macro entry for ${identifier}`);

      const expectedMacroPath = toPosix(path.join("macros", relative));
      assert.equal(
        toPosix(entry.macro_path ?? ""),
        expectedMacroPath,
        `Registry macro_path mismatch for ${identifier}`
      );
    }

    for (const entry of registry.macros ?? []) {
      assert.equal(
        typeof entry.identifier,
        "string",
        "Registry entry must have identifier string"
      );
      assert.equal(
        typeof entry.version,
        "string",
        `Registry entry ${entry.identifier} must include a version string`
      );

      const macroPath = path.join(REPO_ROOT, entry.macro_path ?? "");
      const exists = await fileExists(macroPath);
      assert.ok(exists, `Macro file missing on disk for ${entry.identifier}`);

      if (entry.content_hash) {
        const fileContent = await fs.readFile(macroPath, "utf-8");
        const checksum = crypto
          .createHash("sha256")
          .update(fileContent)
          .digest("hex");
        assert.equal(
          checksum,
          entry.content_hash,
          `Content hash drift detected for ${entry.identifier}`
        );
      }
    }
  });
});
