import express from "express";

export function createApp(rootDirOverride) {
  const app = express();
  const ROOT_DIR = rootDirOverride || process.cwd();

  // Example basic routes (keep or extend with your real ones)
  app.get("/health", (req, res) => {
    res.json({ status: "ok", root: ROOT_DIR });
  });

  return app;
}

// Default app instance for backwards compatibility (npm run dev)
const app = createApp();
export default app;

// If run directly (node src/index.js), start the server
if (import.meta.url === `file://${process.argv[1]}`) {
  const PORT = process.env.PORT || 4000;
  app.listen(PORT, () => {
    console.log(`?? Default Editor running at http://localhost:${PORT}`);
    console.log(`?? Workspace: ${process.cwd()}`);
  });
}
