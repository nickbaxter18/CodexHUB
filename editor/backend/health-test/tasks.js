import express from "express";
import { exec } from "child_process";

const router = express.Router();
const tasks = {};

router.post("/start", (req, res) => {
  const { command } = req.body;
  if (!command) return res.status(400).json({ error: "Command required" });

  const taskId = Date.now().toString();
  const child = exec(command, (err, stdout, stderr) => {
    tasks[taskId] = {
      status: err ? "failed" : "completed",
      stdout,
      stderr,
    };
  });

  tasks[taskId] = { status: "running", stdout: "", stderr: "" };
  res.json({ taskId });
});

router.get("/status", (req, res) => {
  const { taskId } = req.query;
  if (!taskId || !tasks[taskId]) {
    return res.status(404).json({ error: "Task not found" });
  }
  res.json(tasks[taskId]);
});

export default router;