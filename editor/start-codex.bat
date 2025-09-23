@echo off
title CodexHUB Editor + Tunnel

echo ==============================================
echo   🚀 Starting CodexHUB Editor + Tunnel
echo ==============================================

:: Step 1: Start CodexHUB Editor (port 5000 with pnpm)
echo [1/3] Starting CodexHUB Editor...
start "CodexHUB Editor" cmd /k "cd /d C:\Users\Nick\CodexHUB && pnpm run editor:codex"

:: Step 2: Wait for CodexHUB Editor to spin up
echo Waiting 8 seconds for CodexHUB Editor to start...
timeout /t 8 /nobreak >nul

:: Step 3: Start Cloudflare Tunnel
echo [2/3] Starting Cloudflare Tunnel...
start "Cloudflare Tunnel" cmd /k "C:\Users\Nick\.cloudflared\cloudflared.exe" tunnel --config C:\Users\Nick\.cloudflared\config.yml run

:: Step 4: Open in Chrome
timeout /t 5 >nul
echo [3/3] Opening CodexHUB Editor in Chrome...
start "" "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --new-window "http://localhost:5000/editor" "https://codex.udigitai.io/editor"

echo ==============================================
echo ✅ CodexHUB Editor running at:
echo   Local:  http://localhost:5000/editor
echo   Tunnel: https://codex.udigitai.io/editor
echo ==============================================

pause
