import expressModule from "express";
import path from "path";
import { fileURLToPath } from "url";

const express = expressModule.default || expressModule;
const app = express();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = 5000;
const API_KEY = "JncDAe7RBfUSzdF05TOwuPsWrp4hxELVIgG9Nomy";

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

app.listen(PORT, () => {
  console.log(`✅ Server running at http://localhost:${PORT}`);
  console.log(`➡️  Test UI at http://localhost:${PORT}/editor/`);
  console.log(`➡️  Debug at http://localhost:${PORT}/health-test`);
});
