import express from "express";

const router = express.Router();
const API_KEY = process.env.API_KEY || "JncDAe7RBfUSzdF05TOwuPsWrp4hxELVIgG9Nomy";

router.get("/health-test", (req, res) => {
  const key = req.headers["x-api-key"];
  if (key !== API_KEY) {
    return res.status(401).json({ error: "Invalid API key" });
  }
  res.json({ ok: true, message: "CodexBuilder Editor API is alive" });
});

export default router;