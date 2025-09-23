import express from "express";
import fs from "fs";
import path from "path";

const router = express.Router();
const ROOT = process.cwd();

router.get("/tail", (req, res) => {
  try {
    const { path: logPath, lines = 50 } = req.query;
    const fullPath = path.join(ROOT, logPath);
    if (!fs.existsSync(fullPath)) {
      return res.status(404).json({ error: "Log file not found" });
    }
    const content = fs.readFileSync(fullPath, "utf-8").split("\n").slice(-lines).join("\n");
    res.json({ content });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

export default router;