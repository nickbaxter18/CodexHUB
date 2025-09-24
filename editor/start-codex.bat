@echo off
setlocal ENABLEDELAYEDEXPANSION

set "TITLE=CodexHUB Editor Launcher"
title %TITLE%

echo ==================================================
echo   🚀 %TITLE%
echo ==================================================

echo [info] Preparing workspace...
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%.." >nul
set "ROOT_DIR=%CD%"
set "ENV_FILE=%ROOT_DIR%\.env"

set "PORT=5000"
if exist "%ENV_FILE%" (
  for /f "usebackq tokens=1* delims==" %%A in (`findstr /R "^PORT=" "%ENV_FILE%"`) do (
    set "PORT=%%~B"
  )
)
for /f "tokens=*" %%P in ("!PORT!") do set "PORT=%%~P"
if "!PORT!"=="" set "PORT=5000"

set "API_KEY_PRESENT=0"
if exist "%ENV_FILE%" (
  for /f "usebackq tokens=1* delims==" %%A in (`findstr /R "^CODEX_API_KEY=" "%ENV_FILE%"`) do (
    set "API_KEY_PRESENT=1"
  )
)

echo [info] Workspace root : !ROOT_DIR!
echo [info] Editor port    : !PORT!
if exist "!ENV_FILE!" (
  echo [info] Using .env at : !ENV_FILE!
) else (
  echo [warn] .env not found - using environment defaults
)

where pnpm >nul 2>&1
if errorlevel 1 (
  echo [error] pnpm was not found in PATH. Install pnpm from https://pnpm.io/installation and rerun this launcher.
  goto finish
)

if not exist "!ROOT_DIR!\node_modules" (
  echo [setup] Installing dependencies with pnpm install (first run)...
  pnpm install
  if errorlevel 1 (
    echo [error] pnpm install failed. Resolve the issue and rerun the launcher.
    goto finish
  )
)

echo [1/3] Starting CodexHUB Editor server window...
start "CodexHUB Editor" cmd /k "cd /d !ROOT_DIR! && pnpm run editor:codex"

echo Waiting for server to become available...
timeout /t 6 /nobreak >nul

if /I "%CODEX_SKIP_TUNNEL%"=="1" (
  echo [info] Skipping tunnel because CODEX_SKIP_TUNNEL=1
) else (
  call :start_tunnel
)

call :open_browser

echo.
echo ==================================================
echo   ✅ CodexHUB Editor launch complete
if "!API_KEY_PRESENT!"=="0" (
  echo   ⚠️  CODEX_API_KEY missing - set it in .env to allow API calls
)
echo --------------------------------------------------
echo   Local URL : http://localhost:!PORT!/editor
if defined CODEX_TUNNEL_URL (
  echo   Tunnel URL: %CODEX_TUNNEL_URL%
)
echo ==================================================

goto finish

:start_tunnel
setlocal ENABLEDELAYEDEXPANSION
set "TUNNEL_COMMAND="
if defined CODEX_TUNNEL_COMMAND (
  set "TUNNEL_COMMAND=%CODEX_TUNNEL_COMMAND%"
)
if not defined TUNNEL_COMMAND (
  if defined CODEX_TUNNEL_CONFIG (
    set "TUNNEL_COMMAND=cloudflared tunnel --config \"%CODEX_TUNNEL_CONFIG%\" run"
  )
)
if not defined TUNNEL_COMMAND (
  set "TUNNEL_COMMAND=cloudflared tunnel --url http://localhost:!PORT!"
  where cloudflared >nul 2>&1
  if errorlevel 1 (
    echo [warn] cloudflared was not found in PATH. Skipping tunnel startup.
    endlocal
    exit /b 0
  )
)

echo [2/3] Starting tunnel window...
echo         !TUNNEL_COMMAND!
start "CodexHUB Tunnel" cmd /k "cd /d !ROOT_DIR! && !TUNNEL_COMMAND!"
endlocal
exit /b 0

:open_browser
setlocal ENABLEDELAYEDEXPANSION
set "LOCAL_URL=http://localhost:!PORT!/editor"
echo [3/3] Opening browser tabs...
if defined CODEX_BROWSER (
  start "" "%CODEX_BROWSER%" "!LOCAL_URL!"
) else (
  start "" "!LOCAL_URL!"
)
if defined CODEX_TUNNEL_URL (
  if defined CODEX_BROWSER (
    start "" "%CODEX_BROWSER%" "%CODEX_TUNNEL_URL%"
  ) else (
    start "" "%CODEX_TUNNEL_URL%"
  )
)
endlocal
exit /b 0

:finish
popd >nul
endlocal
pause
