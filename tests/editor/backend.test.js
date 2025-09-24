import { setTimeout as delay } from "timers/promises";
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..");

const API_KEY = "codex-test-key";
process.env.CODEX_API_KEY = API_KEY;

const { startServer } = await import("../../editor/codex-editor.js");

const defaultHeaders = {
  "Content-Type": "application/json",
  "x-api-key": API_KEY,
};

function toFsPath(workspacePath) {
  return path.resolve(repoRoot, workspacePath.split("/").join(path.sep));
}

test("Codex editor backend supports core workspace operations", async (t) => {
  const serverInfo = startServer({ port: 0, host: "127.0.0.1" });
  await serverInfo.ready;
  const baseHost = serverInfo.host === "0.0.0.0" ? "127.0.0.1" : serverInfo.host;
  const baseUrl = `http://${baseHost}:${serverInfo.port}`;

  const testFolder = `editor/.editor-test-${Date.now()}`;
  const testFolderFs = toFsPath(testFolder);

  t.after(async () => {
    await new Promise((resolve) => serverInfo.server.close(resolve));
    await fs.rm(testFolderFs, { recursive: true, force: true });
  });

  const unauthorized = await fetch(`${baseUrl}/list?dir=.`);
  assert.strictEqual(unauthorized.status, 401);

  const listResp = await fetch(`${baseUrl}/list?dir=editor`, {
    headers: { "x-api-key": API_KEY },
  });
  assert.strictEqual(listResp.status, 200);
  const listData = await listResp.json();
  assert.ok(Array.isArray(listData.files));
  assert.ok(listData.files.some((entry) => entry.name === "README.md"));

  const folderResp = await fetch(`${baseUrl}/create/folder`, {
    method: "POST",
    headers: defaultHeaders,
    body: JSON.stringify({ path: testFolder }),
  });
  assert.strictEqual(folderResp.status, 200);

  const filePath = `${testFolder}/sample.txt`;
  const initialContent = "hello world from test";
  const saveResp = await fetch(`${baseUrl}/file`, {
    method: "POST",
    headers: defaultHeaders,
    body: JSON.stringify({ path: filePath, content: initialContent }),
  });
  assert.strictEqual(saveResp.status, 200);

  const fileResp = await fetch(`${baseUrl}/file?path=${encodeURIComponent(filePath)}`, {
    headers: { "x-api-key": API_KEY },
  });
  assert.strictEqual(fileResp.status, 200);
  const fileData = await fileResp.json();
  assert.strictEqual(fileData.content, initialContent);

  const searchResp = await fetch(
    `${baseUrl}/search?query=${encodeURIComponent("hello world from test")}`,
    {
      headers: { "x-api-key": API_KEY },
    },
  );
  assert.strictEqual(searchResp.status, 200);
  const searchData = await searchResp.json();
  assert.ok(searchData.matches.some((match) => match.path.endsWith("sample.txt")));

  const replaceResp = await fetch(`${baseUrl}/replace`, {
    method: "POST",
    headers: defaultHeaders,
    body: JSON.stringify({ query: "hello", replace: "hi" }),
  });
  assert.strictEqual(replaceResp.status, 200);

  const replacedFileResp = await fetch(`${baseUrl}/file?path=${encodeURIComponent(filePath)}`, {
    headers: { "x-api-key": API_KEY },
  });
  const replacedFile = await replacedFileResp.json();
  assert.ok(replacedFile.content.includes("hi world from test"));

  const movedPath = `${testFolder}/renamed.txt`;
  const moveResp = await fetch(`${baseUrl}/move`, {
    method: "POST",
    headers: defaultHeaders,
    body: JSON.stringify({ src: filePath, dest: movedPath }),
  });
  assert.strictEqual(moveResp.status, 200);

  const deleteResp = await fetch(`${baseUrl}/delete`, {
    method: "POST",
    headers: defaultHeaders,
    body: JSON.stringify({ path: movedPath }),
  });
  assert.strictEqual(deleteResp.status, 200);

  const taskResp = await fetch(`${baseUrl}/task/start`, {
    method: "POST",
    headers: defaultHeaders,
    body: JSON.stringify({ command: "node -e \"console.log('task ok')\"" }),
  });
  assert.strictEqual(taskResp.status, 200);
  const taskData = await taskResp.json();
  assert.ok(taskData.taskId);

  let taskStatus;
  for (let attempt = 0; attempt < 20; attempt += 1) {
    const statusResp = await fetch(
      `${baseUrl}/task/status?taskId=${encodeURIComponent(taskData.taskId)}`,
      { headers: { "x-api-key": API_KEY } },
    );
    assert.strictEqual(statusResp.status, 200);
    taskStatus = await statusResp.json();
    if (taskStatus.status === "done" || taskStatus.status === "failed") {
      break;
    }
    await delay(50);
  }

  assert.ok(taskStatus, "Task status was not retrieved");
  assert.strictEqual(taskStatus.status, "done");
  assert.ok(taskStatus.stdout.includes("task ok"));
});
