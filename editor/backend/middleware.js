import dotenv from "dotenv";
dotenv.config();

export function checkApiKey(req, res, next) {
  const provided = req.header("x-api-key");
  const expected = process.env.CODEX_API_KEY;

  if (!provided) {
    return res.status(401).json({ error: "Unauthorized: Missing API key" });
  }
  if (provided !== expected) {
    return res.status(403).json({ error: "Forbidden: Invalid API key" });
  }

  next();
}
