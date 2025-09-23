import expressModule from "express";
import path from "path";
import { fileURLToPath } from "url";
import { exec } from "child_process";

const express = expressModule.default || expressModule;
const app = express();

// Middleware
app.use(express.json());

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = 5000;
const API_KEY = "JncDAe7RBfUSzdF05TOwuPsWrp4hxELVIgG9Nomy";
let tasks = {};

// ✅ Explicit path to your editor folder
const editorPath = "C:/Users/Nick/CodexBuilder/editor";
app.use("/editor", express.static(editorPath));

// ✅ Default: redirect /editor → codex-editor.html
app.get("/editor", (req, res) => {
  res.sendFile(path.join(editorPath, "codex-editor.html"));
});

// ✅ Debug endpoint
app.get("/health-test", (req, res) => {
  const key = req.headers["x-api-key"];
  if (key !== API_KEY) {
    return res.status(401).json({ error: "Invalid API key" });
  }
  res.json({ ok: true, message: "CodexBuilder Editor API is alive" });
});

// ✅ Cursor CLI Integration
app.post("/cursor-agent", (req, res) => {
  const key = req.headers["x-api-key"];
  if (key !== API_KEY) {
    return res.status(401).json({ error: "Invalid API key" });
  }
  
  const { query } = req.body;
  if (!query) return res.status(400).json({ error: "Missing query" });
  
  const command = `wsl cursor-agent "${query}"`;
  const taskId = Date.now().toString();
  
  const child = exec(command, { cwd: "C:/Users/Nick/CodexBuilder" });
  
  tasks[taskId] = { status: "running", stdout: "", stderr: "" };
  child.stdout.on("data", (d) => (tasks[taskId].stdout += d));
  child.stderr.on("data", (d) => (tasks[taskId].stderr += d));
  child.on("close", () => (tasks[taskId].status = "done"));
  
  res.json({ message: "Cursor Agent started", taskId });
});

// ✅ Task status endpoint
app.get("/task-status", (req, res) => {
  const key = req.headers["x-api-key"];
  if (key !== API_KEY) {
    return res.status(401).json({ error: "Invalid API key" });
  }
  
  const { taskId } = req.query;
  if (!taskId) return res.status(400).json({ error: "Missing taskId" });
  
  const task = tasks[taskId];
  if (!task) {
    return res.status(404).json({ error: "Task not found" });
  }
  res.json(task);
});

app.listen(PORT, () => {
  console.log(`✅ Server running at http://localhost:${PORT}`);
  console.log(`➡️  Test UI at http://localhost:${PORT}/editor/`);
  console.log(`➡️  Debug at http://localhost:${PORT}/health-test`);
});
