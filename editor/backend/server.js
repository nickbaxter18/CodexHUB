import { startServer } from "../codex-editor.js";

function parseCliOptions() {
  const options = {};
  for (const arg of process.argv.slice(2)) {
    const [key, value] = arg.split("=");
    if (!value) {
      continue;
    }
    if (key === "--port" || key === "-p") {
      options.port = Number(value);
    }
    if (key === "--host" || key === "-H") {
      options.host = value;
    }
  }
  return options;
}

function main() {
  try {
    startServer(parseCliOptions());
  } catch (error) {
    console.error("Failed to start CodexHUB Editor backend:", error);
    process.exit(1);
  }
}

main();
