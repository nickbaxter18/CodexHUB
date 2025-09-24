import { loadEnvironment } from "./config.js";

loadEnvironment();

let missingKeyWarningShown = false;

export function checkApiKey(req, res, next) {
  const provided = req.header("x-api-key");
  const expected = process.env.CODEX_API_KEY;

  if (!expected) {
    if (!missingKeyWarningShown) {
      console.error(
        "❌ CODEX_API_KEY is not set. Configure it in your .env file so the editor can authenticate requests.",
      );
      missingKeyWarningShown = true;
    }
    return res.status(500).json({ error: "Server misconfigured: CODEX_API_KEY missing" });
  }

  if (!provided) {
    return res.status(401).json({ error: "Unauthorized: Missing API key" });
  }
  if (provided !== expected) {
    return res.status(403).json({ error: "Forbidden: Invalid API key" });
  }

  next();
}
