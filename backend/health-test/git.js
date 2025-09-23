import express from "express";
import simpleGit from "simple-git";
import path from "path";

const router = express.Router();
const git = simpleGit(path.resolve(process.cwd()));

router.get("/status", async (req, res) => {
  try {
    const status = await git.status();
    res.json(status);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.get("/diff", async (req, res) => {
  try {
    const { path: filePath } = req.query;
    const diff = await git.diff([filePath]);
    res.json({ diff });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.get("/log", async (req, res) => {
  try {
    const limit = parseInt(req.query.limit || "10", 10);
    const logs = await git.log({ maxCount: limit });
    res.json(logs);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.post("/reset", async (req, res) => {
  try {
    await git.reset(["--hard"]);
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

export default router;