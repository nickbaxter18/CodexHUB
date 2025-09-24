import expressModule from "express";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { spawn } from "child_process";

import dotenv from "dotenv";

dotenv.config();

const express = expressModule.default || expressModule;
const app = express();

app.use(express.json());

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = Number.parseInt(process.env.EDITOR_PORT || "5000", 10);
const API_KEY = process.env.EDITOR_API_KEY;
const cursorAgentCommand = process.env.CURSOR_AGENT_COMMAND || "cursor-agent";
const cursorAgentCwd = path.resolve(
  process.env.CURSOR_AGENT_CWD || path.join(__dirname, ".."),
);

const tasks = new Map();

const tokenizeCommand = (value) => {
  const tokens = [];
  let current = "";
  let quote = null;
  let escape = false;

  for (const char of value.trim()) {
    if (escape) {
      current += char;
      escape = false;
      continue;
    }

    if (char === "\\") {
      escape = true;
      continue;
    }

    if (quote) {
      if (char === quote) {
        quote = null;
      } else {
        current += char;
      }
      continue;
    }

    if (char === "\"" || char === "'") {
      quote = char;
      continue;
    }

    if (char === " " || char === "\t") {
      if (current) {
        tokens.push(current);
        current = "";
      }
      continue;
    }

    current += char;
  }

  if (current) {
    tokens.push(current);
  }

  return tokens;
};

const commandParts = tokenizeCommand(cursorAgentCommand);
const [commandBinary, ...defaultArgs] = commandParts;

const resolveEditorPath = () => {
  const configuredPath = process.env.EDITOR_STATIC_DIR;
  const candidate = path.resolve(
    configuredPath && configuredPath.trim().length > 0
      ? configuredPath
      : path.join(__dirname, "../editor"),
  );

  if (!fs.existsSync(candidate)) {
    console.warn(
      `⚠️ Editor static directory "${candidate}" does not exist. ` +
        "Update EDITOR_STATIC_DIR to point at the built editor assets.",
    );
  }

  return candidate;
};

const editorPath = resolveEditorPath();
app.use("/editor", express.static(editorPath));

app.get("/editor", (req, res) => {
  res.sendFile(path.join(editorPath, "codex-editor.html"));
});

const ensureApiKey = (req, res) => {
  if (!API_KEY) {
    res
      .status(503)
      .json({ error: "Editor API key is not configured. Set EDITOR_API_KEY." });
    return false;
  }

  const key = req.headers["x-api-key"];
  if (!key) {
    res.status(401).json({ error: "Missing API key" });
    return false;
  }

  if (key !== API_KEY) {
    res.status(403).json({ error: "Invalid API key" });
    return false;
  }

  return true;
};

app.get("/health-test", (req, res) => {
  if (!ensureApiKey(req, res)) {
    return;
  }

  res.json({ ok: true, message: "CodexBuilder Editor API is alive" });
});

app.post("/cursor-agent", (req, res) => {
  if (!ensureApiKey(req, res)) {
    return;
  }

  const { query } = req.body || {};
  if (!query) {
    res.status(400).json({ error: "Missing query" });
    return;
  }

  if (!commandBinary) {
    res.status(500).json({ error: "Cursor agent command is not configured." });
    return;
  }

  const taskId = Date.now().toString();
  const args = [...defaultArgs, String(query)];

  const child = spawn(commandBinary, args, {
    cwd: cursorAgentCwd,
    stdio: ["ignore", "pipe", "pipe"],
  });

  tasks.set(taskId, { status: "running", stdout: "", stderr: "" });

  child.stdout.on("data", (chunk) => {
    const task = tasks.get(taskId);
    if (task) {
      task.stdout += chunk;
    }
  });

  child.stderr.on("data", (chunk) => {
    const task = tasks.get(taskId);
    if (task) {
      task.stderr += chunk;
    }
  });

  child.on("error", (error) => {
    const task = tasks.get(taskId);
    if (task) {
      task.status = "error";
      task.stderr += `${error.message}\n`;
      task.exitCode = task.exitCode ?? 1;
    }
  });

  child.on("close", (code) => {
    const task = tasks.get(taskId);
    if (task) {
      task.status = code === 0 ? "done" : "error";
      task.exitCode = code;
    }
  });

  res.json({ message: "Cursor Agent started", taskId });
});

app.get("/task-status", (req, res) => {
  if (!ensureApiKey(req, res)) {
    return;
  }

  const { taskId } = req.query;
  if (!taskId) {
    res.status(400).json({ error: "Missing taskId" });
    return;
  }

  const task = tasks.get(String(taskId));
  if (!task) {
    res.status(404).json({ error: "Task not found" });
    return;
  }

  res.json(task);
});

app.listen(PORT, () => {
  console.log(`✅ Server running at http://localhost:${PORT}`);
  console.log(`➡️  Test UI at http://localhost:${PORT}/editor/`);
  console.log(`➡️  Debug at http://localhost:${PORT}/health-test`);
});
