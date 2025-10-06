@echo off
setlocal

REM Navigate to the repo root (contains pyproject.toml)
cd /d "%~dp0\.."

where uv >nul 2>&1
if errorlevel 1 (
  echo uv is required to set up the agent. Install it from https://astral.sh/uv/install.sh
  exit /b 1
)

uv sync --extra test
