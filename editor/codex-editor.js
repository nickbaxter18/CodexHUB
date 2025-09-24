import fs from "fs";
import path from "path";
import express from "express";
import { exec } from "child_process";
import { fileURLToPath } from "url";
import {
  isIgnoredPath,
  loadEnvironment,
  resolveWorkspacePath,
  resolveWorkspaceRoot,
} from "./backend/config.js";
import { checkApiKey } from "./backend/middleware.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

loadEnvironment();

const DEFAULT_PORT = 5000;
const DEFAULT_HOST = "0.0.0.0";
const JSON_LIMIT = process.env.CODEX_JSON_LIMIT || "10mb";
const FORM_LIMIT = process.env.CODEX_FORM_LIMIT || "10mb";
const TASK_MAX_BUFFER = Number(process.env.CODEX_TASK_MAX_BUFFER ?? 10 * 1024 * 1024);

let warnedAboutMissingApiKey = false;

function warnMissingApiKey() {
  if (!process.env.CODEX_API_KEY && !warnedAboutMissingApiKey) {
    console.warn(
      "⚠️  CODEX_API_KEY is not configured. Set it in your .env file so authenticated requests can succeed.",
    );
    warnedAboutMissingApiKey = true;
  }
}

function sanitizeError(error) {
  if (error.code === "INVALID_PATH") {
    return { status: 400, message: error.message };
  }
  return { status: 500, message: error.message || "Unexpected error" };
}

export function createApp() {
  const app = express();
  const ROOT_DIR = resolveWorkspaceRoot();
  const tasks = {};
  createApp.ROOT_DIR = ROOT_DIR;

  warnMissingApiKey();

  app.use(express.json({ limit: JSON_LIMIT }));
  app.use(express.urlencoded({ extended: true, limit: FORM_LIMIT }));

  // Serve /editor folder as static
  app.use("/editor", express.static(__dirname));

  // Serve codex-editor.html directly at /editor
  app.get("/editor", (req, res) => {
    res.sendFile(path.resolve(__dirname, "codex-editor.html"));
  });

  app.get("/", (req, res) => {
    res.redirect(302, "/editor");
  });

  // Health check
  app.get("/health", (req, res) => {
    res.json({ status: "ok", uptime: process.uptime(), root: ROOT_DIR });
  });

  // === SAFE PATH ===
  function safePath(p = ".") {
    return resolveWorkspacePath(ROOT_DIR, p);
  }

  // === FILE + DIR ROUTES ===
  app.get("/list", checkApiKey, (req, res) => {
    try {
      const requested = req.query.dir || ".";
      const dir = safePath(requested);
      if (!fs.existsSync(dir)) {
        return res.status(404).json({ error: "Not found" });
      }

      const files = fs.readdirSync(dir).map((f) => {
        const stat = fs.statSync(path.join(dir, f));
        return { name: f, type: stat.isDirectory() ? "dir" : "file" };
      });

      const relativeDir = path.relative(ROOT_DIR, dir) || ".";
      res.json({ dir: relativeDir.replace(/\\/g, "/"), files });
    } catch (error) {
      const { status, message } = sanitizeError(error);
      res.status(status).json({ error: message });
    }
  });

  app.get("/file", checkApiKey, (req, res) => {
    try {
      if (!req.query.path) {
        return res.status(400).json({ error: "Missing path" });
      }
      const filePath = safePath(req.query.path);
      if (!fs.existsSync(filePath)) {
        return res.status(404).json({ error: "Not found" });
      }
      res.json({
        path: req.query.path,
        content: fs.readFileSync(filePath, "utf8"),
      });
    } catch (error) {
      const { status, message } = sanitizeError(error);
      res.status(status).json({ error: message });
    }
  });

  app.post("/file", checkApiKey, (req, res) => {
    try {
      const { path: filePath, content } = req.body;
      if (!filePath) {
        return res.status(400).json({ error: "Missing path" });
      }
      const target = safePath(filePath);
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.writeFileSync(target, content ?? "", "utf8");
      res.json({ message: "File saved", path: filePath });
    } catch (error) {
      const { status, message } = sanitizeError(error);
      res.status(status).json({ error: message });
    }
  });

  app.post("/create/file", checkApiKey, (req, res) => {
    try {
      if (!req.body.path) {
        return res.status(400).json({ error: "Missing path" });
      }
      const target = safePath(req.body.path);
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.writeFileSync(target, "", "utf8");
      res.json({ message: "File created", path: req.body.path });
    } catch (error) {
      const { status, message } = sanitizeError(error);
      res.status(status).json({ error: message });
    }
  });

  app.post("/create/folder", checkApiKey, (req, res) => {
    try {
      if (!req.body.path) {
        return res.status(400).json({ error: "Missing path" });
      }
      fs.mkdirSync(safePath(req.body.path), { recursive: true });
      res.json({ message: "Folder created", path: req.body.path });
    } catch (error) {
      const { status, message } = sanitizeError(error);
      res.status(status).json({ error: message });
    }
  });

  app.post("/delete", checkApiKey, (req, res) => {
    try {
      if (!req.body.path) {
        return res.status(400).json({ error: "Missing path" });
      }
      const p = safePath(req.body.path);
      if (!fs.existsSync(p)) {
        return res.status(404).json({ error: "Not found" });
      }
      if (req.body.recursive) {
        fs.rmSync(p, { recursive: true, force: true });
      } else {
        fs.unlinkSync(p);
      }
      res.json({ message: "Deleted", path: req.body.path });
    } catch (error) {
      const { status, message } = sanitizeError(error);
      res.status(status).json({ error: message });
    }
  });

  app.post("/move", checkApiKey, (req, res) => {
    try {
      const { src, dest } = req.body;
      if (!src || !dest) {
        return res.status(400).json({ error: "Missing src/dest" });
      }
      const sourcePath = safePath(src);
      if (!fs.existsSync(sourcePath)) {
        return res.status(404).json({ error: "Source not found" });
      }
      const destinationPath = safePath(dest);
      fs.mkdirSync(path.dirname(destinationPath), { recursive: true });
      fs.renameSync(sourcePath, destinationPath);
      res.json({ message: "Moved", src, dest });
    } catch (error) {
      const { status, message } = sanitizeError(error);
      res.status(status).json({ error: message });
    }
  });

  // === SEARCH + REPLACE ===
  app.get("/search", checkApiKey, (req, res) => {
    try {
      const query = req.query.query;
      if (!query) {
        return res.status(400).json({ error: "Missing query" });
      }

      const matches = [];
      function searchDir(dir) {
        let entries = [];
        try {
          entries = fs.readdirSync(dir);
        } catch (error) {
          return;
        }
        entries.forEach((file) => {
          const p = path.join(dir, file);
          if (isIgnoredPath(ROOT_DIR, p)) {
            return;
          }
          let stat;
          try {
            stat = fs.statSync(p);
          } catch (error) {
            return;
          }
          if (stat.isDirectory()) {
            searchDir(p);
            return;
          }
          let lines;
          try {
            lines = fs.readFileSync(p, "utf8").split("\n");
          } catch (error) {
            return;
          }
          lines.forEach((line, i) => {
            if (line.includes(query)) {
              matches.push({
                path: path.relative(ROOT_DIR, p).replace(/\\/g, "/"),
                line: i + 1,
                text: line,
              });
            }
          });
        });
      }

      searchDir(ROOT_DIR);
      res.json({ matches });
    } catch (error) {
      const { status, message } = sanitizeError(error);
      res.status(status).json({ error: message });
    }
  });

  app.post("/replace", checkApiKey, (req, res) => {
    try {
      const { query, replace } = req.body;
      if (!query) {
        return res.status(400).json({ error: "Missing query" });
      }

      let count = 0;
      function replaceDir(dir) {
        let entries = [];
        try {
          entries = fs.readdirSync(dir);
        } catch (error) {
          return;
        }
        entries.forEach((file) => {
          const p = path.join(dir, file);
          if (isIgnoredPath(ROOT_DIR, p)) {
            return;
          }
          let stat;
          try {
            stat = fs.statSync(p);
          } catch (error) {
            return;
          }
          if (stat.isDirectory()) {
            replaceDir(p);
            return;
          }
          let content;
          try {
            content = fs.readFileSync(p, "utf8");
          } catch (error) {
            return;
          }
          if (content.includes(query)) {
            fs.writeFileSync(p, content.split(query).join(replace ?? ""), "utf8");
            count++;
          }
        });
      }

      replaceDir(ROOT_DIR);
      res.json({ message: `Replaced in ${count} files` });
    } catch (error) {
      const { status, message } = sanitizeError(error);
      res.status(status).json({ error: message });
    }
  });

  // === LOGS, TASKS, GIT ===
  app.get("/logs/tail", checkApiKey, (req, res) => {
    try {
      const { path: logPath, lines = 50 } = req.query;
      if (!logPath) {
        return res.status(400).json({ error: "Missing log path" });
      }
      const fullPath = safePath(logPath);
      if (!fs.existsSync(fullPath)) {
        return res.status(404).json({ error: "Not found" });
      }
      const lineCount = Number(lines) || 50;
      const content = fs
        .readFileSync(fullPath, "utf8")
        .split("\n")
        .slice(-lineCount)
        .join("\n");
      res.json({ content });
    } catch (error) {
      const { status, message } = sanitizeError(error);
      res.status(status).json({ error: message });
    }
  });

  app.post("/task/start", checkApiKey, (req, res) => {
    try {
      if (!req.body.command) {
        return res.status(400).json({ error: "Missing command" });
      }
      const id = Date.now().toString();
      const child = exec(req.body.command, {
        cwd: ROOT_DIR,
        maxBuffer: TASK_MAX_BUFFER,
      });
      tasks[id] = { status: "running", stdout: "", stderr: "" };
      child.stdout?.on("data", (d) => (tasks[id].stdout += d));
      child.stderr?.on("data", (d) => (tasks[id].stderr += d));
      child.on("close", (code) => {
        tasks[id].status = code === 0 ? "done" : "failed";
      });
      res.json({ message: "Task started", taskId: id });
    } catch (error) {
      const { status, message } = sanitizeError(error);
      res.status(status).json({ error: message });
    }
  });

  app.get("/task/status", checkApiKey, (req, res) => {
    try {
      if (!req.query.taskId) {
        return res.status(400).json({ error: "Missing taskId" });
      }
      const task = tasks[req.query.taskId];
      if (!task) {
        return res.status(404).json({ error: "Task not found" });
      }
      res.json(task);
    } catch (error) {
      const { status, message } = sanitizeError(error);
      res.status(status).json({ error: message });
    }
  });

  app.get("/git/status", checkApiKey, (req, res) => {
    exec("git status", { cwd: ROOT_DIR }, (err, stdout, stderr) => {
      if (err) {
        res.json({ stdout, stderr, error: err.message });
        return;
      }
      res.json({ stdout, stderr, error: null });
    });
  });

  // === CURSOR CLI INTEGRATION ===
  app.post("/cursor-agent", checkApiKey, (req, res) => {
    try {
      const { query } = req.body;
      if (!query) {
        return res.status(400).json({ error: "Missing query" });
      }

      const cursorAgentCommand = process.env.CURSOR_AGENT_COMMAND;
      if (!cursorAgentCommand) {
        return res.status(501).json({ error: "Cursor agent command not configured" });
      }

      const id = Date.now().toString();
      const command = `${cursorAgentCommand} ${JSON.stringify(query)}`;
      const child = exec(command, {
        cwd: ROOT_DIR,
        maxBuffer: TASK_MAX_BUFFER,
      });

      tasks[id] = { status: "running", stdout: "", stderr: "" };
      child.stdout?.on("data", (d) => (tasks[id].stdout += d));
      child.stderr?.on("data", (d) => (tasks[id].stderr += d));
      child.on("close", (code) => {
        tasks[id].status = code === 0 ? "done" : "failed";
      });

      res.json({ message: "Cursor Agent started", taskId: id });
    } catch (error) {
      const { status, message } = sanitizeError(error);
      res.status(status).json({ error: message });
    }
  });

  return app;
}

export function startServer(options = {}) {
  const app = createApp();
  const requestedPort = options.port ?? process.env.PORT ?? DEFAULT_PORT;
  const portNumber = Number(requestedPort);
  const host = options.host ?? process.env.HOST ?? DEFAULT_HOST;
  const server = app.listen(portNumber, host);
  const serverInfo = { app, server, host, port: portNumber };

  serverInfo.ready = new Promise((resolve, reject) => {
    const onListening = () => {
      server.off("error", onError);
      const address = server.address();
      const actualPort = typeof address === "object" && address ? address.port : portNumber;
      serverInfo.port = actualPort;
      const workspaceRoot = createApp.ROOT_DIR || resolveWorkspaceRoot();
      const displayHost = host === "0.0.0.0" || host === "::" ? "localhost" : host;
      console.log(`🚀 CodexHUB Editor running at http://${displayHost}:${actualPort}`);
      if (displayHost !== host) {
        console.log(`🌐 Listening on ${host}:${actualPort}`);
      }
      console.log(`📂 Workspace: ${workspaceRoot}`);
      console.log(`📝 Editor:  http://${displayHost}:${actualPort}/editor`);
      console.log(`❤️ Health:  http://${displayHost}:${actualPort}/health`);
      resolve(serverInfo);
    };

    const onError = (error) => {
      server.off("listening", onListening);
      reject(error);
    };

    server.once("listening", onListening);
    server.once("error", onError);
  });

  server.on("error", (error) => {
    console.error("❌ Failed to start CodexHUB Editor server", error);
  });

  return serverInfo;
}

const isDirectExecution = path.resolve(process.argv[1] || "") === __filename;

if (isDirectExecution) {
  const info = startServer();
  info.ready?.catch((error) => {
    console.error("❌ CodexHUB Editor failed to start", error);
    process.exit(1);
  });
}
