import express from "express";

const router = express.Router();
const API_KEY = process.env.EDITOR_API_KEY;

router.get("/health-test", (req, res) => {
  if (!API_KEY) {
    return res
      .status(503)
      .json({ error: "Editor API key is not configured. Set EDITOR_API_KEY." });
  }

  const key = req.headers["x-api-key"];
  if (!key) {
    return res.status(401).json({ error: "Missing API key" });
  }

  if (key !== API_KEY) {
    return res.status(403).json({ error: "Invalid API key" });
  }

  res.json({ ok: true, message: "CodexBuilder Editor API is alive" });
});

export default router;
