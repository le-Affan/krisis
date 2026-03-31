@echo off
REM ═══════════════════════════════════════════════════════════════════
REM  Krisis — Windows Startup Wrapper
REM  Delegates to scripts/startup.sh via Git Bash / WSL
REM
REM  Usage:
REM    scripts\startup.bat                  (production, default)
REM    scripts\startup.bat --dev            (development mode)
REM    scripts\startup.bat --monitoring     (production + monitoring)
REM    scripts\startup.bat --rebuild        (force rebuild)
REM    scripts\startup.bat --down           (graceful shutdown)
REM    scripts\startup.bat --down --purge   (shutdown + delete volumes)
REM ═══════════════════════════════════════════════════════════════════

setlocal

REM Resolve project root (one level up from scripts/)
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%.."
set "PROJECT_ROOT=%CD%"
popd

REM Try Git Bash first, then WSL
where bash >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [Krisis] Running startup via bash...
    bash "%PROJECT_ROOT%\scripts\startup.sh" %*
    exit /b %ERRORLEVEL%
)

where wsl >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [Krisis] Running startup via WSL...
    wsl bash ./scripts/startup.sh %*
    exit /b %ERRORLEVEL%
)

echo.
echo [ERROR] Neither bash nor WSL found.
echo         Install Git for Windows (includes Git Bash) or enable WSL.
echo         https://gitforwindows.org/
echo.
exit /b 1
