import express from "express";
import fs from "fs";
import path from "path";

const router = express.Router();
const ROOT = process.cwd();

router.get("/list", (req, res) => {
  const dir = req.query.dir || "/";
  const fullPath = path.join(ROOT, dir);
  try {
    const files = fs.readdirSync(fullPath).map(name => ({
      name,
      type: fs.statSync(path.join(fullPath, name)).isDirectory() ? "dir" : "file"
    }));
    res.json({ dir, files });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.get("/file", (req, res) => {
  try {
    const { path: filePath } = req.query;
    const content = fs.readFileSync(path.join(ROOT, filePath), "utf-8");
    res.json({ path: filePath, content });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.post("/file", (req, res) => {
  const { path: filePath, content } = req.body;
  try {
    fs.writeFileSync(path.join(ROOT, filePath), content, "utf-8");
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.post("/create/file", (req, res) => {
  const { path: filePath } = req.body;
  try {
    fs.writeFileSync(path.join(ROOT, filePath), "");
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.post("/create/folder", (req, res) => {
  const { path: folderPath } = req.body;
  try {
    fs.mkdirSync(path.join(ROOT, folderPath), { recursive: true });
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.post("/delete", (req, res) => {
  const { path: targetPath, recursive } = req.body;
  try {
    const fullPath = path.join(ROOT, targetPath);
    if (fs.statSync(fullPath).isDirectory()) {
      fs.rmSync(fullPath, { recursive: !!recursive, force: true });
    } else {
      fs.unlinkSync(fullPath);
    }
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.post("/move", (req, res) => {
  const { src, dest } = req.body;
  try {
    fs.renameSync(path.join(ROOT, src), path.join(ROOT, dest));
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.get("/search", (req, res) => {
  const { query, dir = "/" } = req.query;
  try {
    const results = [];
    const walk = (folder) => {
      fs.readdirSync(folder).forEach((file) => {
        const full = path.join(folder, file);
        if (fs.statSync(full).isDirectory()) return walk(full);
        const lines = fs.readFileSync(full, "utf-8").split("\n");
        lines.forEach((line, idx) => {
          if (line.includes(query)) {
            results.push({ path: full, line: idx + 1, text: line });
          }
        });
      });
    };
    walk(path.join(ROOT, dir));
    res.json({ matches: results });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.post("/replace", (req, res) => {
  const { query, replace, dir = "/" } = req.body;
  try {
    const walk = (folder) => {
      fs.readdirSync(folder).forEach((file) => {
        const full = path.join(folder, file);
        if (fs.statSync(full).isDirectory()) return walk(full);
        let content = fs.readFileSync(full, "utf-8");
        if (content.includes(query)) {
          fs.writeFileSync(full, content.replaceAll(query, replace));
        }
      });
    };
    walk(path.join(ROOT, dir));
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

export default router;