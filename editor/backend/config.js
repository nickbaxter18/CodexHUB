import fs from "fs";
import path from "path";
import dotenv from "dotenv";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const EDITOR_DIR = path.resolve(__dirname, "..");
const REPO_ROOT = path.resolve(EDITOR_DIR, "..");

const DEFAULT_ENV_CANDIDATES = [
  process.env.CODEX_ENV_PATH,
  path.resolve(EDITOR_DIR, ".env"),
  path.resolve(REPO_ROOT, ".env"),
].filter(Boolean);

const DEFAULT_IGNORE_DIRS = [
  ".git",
  ".hg",
  ".svn",
  "node_modules",
  ".pnpm-store",
  "vendor",
  "dist",
  "build",
  ".next",
  ".cache",
  ".turbo",
  "__pycache__",
  ".pytest_cache",
];

let cachedIgnoreSet = null;

function getIgnoreSet() {
  if (cachedIgnoreSet) {
    return cachedIgnoreSet;
  }

  const envIgnores = (process.env.CODEX_IGNORE_DIRS || "")
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean);

  cachedIgnoreSet = new Set([...DEFAULT_IGNORE_DIRS, ...envIgnores]);
  return cachedIgnoreSet;
}

export function loadEnvironment(candidates = DEFAULT_ENV_CANDIDATES) {
  for (const candidate of candidates) {
    try {
      const resolved = path.resolve(candidate);
      if (fs.existsSync(resolved) && fs.statSync(resolved).isFile()) {
        dotenv.config({ path: resolved });
        return resolved;
      }
    } catch (error) {
      // Ignore inaccessible candidates and try the next one
    }
  }

  dotenv.config();
  return null;
}

export function resolveWorkspaceRoot() {
  const candidates = [
    process.env.CODEX_WORKSPACE_ROOT,
    process.env.GITHUB_WORKSPACE,
    REPO_ROOT,
  ].filter(Boolean);

  for (const candidate of candidates) {
    try {
      const resolved = path.resolve(candidate);
      if (fs.existsSync(resolved) && fs.statSync(resolved).isDirectory()) {
        return resolved;
      }
    } catch (error) {
      // Skip invalid candidates
    }
  }

  return process.cwd();
}

export function resolveWorkspacePath(rootDir, requestedPath = ".") {
  const target = path.resolve(rootDir, requestedPath);
  const relative = path.relative(rootDir, target);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    const error = new Error("Invalid path outside workspace");
    error.code = "INVALID_PATH";
    throw error;
  }
  return target;
}

export function isIgnoredPath(rootDir, targetPath) {
  const ignoreSet = getIgnoreSet();
  const relative = path.relative(rootDir, targetPath);
  if (relative.startsWith("..")) {
    return true;
  }

  return relative
    .split(path.sep)
    .some((segment) => ignoreSet.has(segment));
}

export function getEditorDirectory() {
  return EDITOR_DIR;
}

export function getRepoRoot() {
  return REPO_ROOT;
}
