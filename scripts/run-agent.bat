@echo off
setlocal

REM Navigate to the repository root (contains pyproject.toml)
cd /d %~dp0\..

where uv >nul 2>&1
if errorlevel 1 (
  echo uv is required to run the agent. Install it from https://astral.sh/uv/install.sh
  exit /b 1
)

uv run python -m agent
