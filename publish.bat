@echo off
REM ============================================================
REM  One-click publish for Edge Studio
REM  Commits the latest odds files and pushes to GitHub.
REM  GitHub Actions then rebuilds and redeploys the live site:
REM    https://techneva.github.io/edge-studio/
REM  (No Python needed locally — the rebuild happens in the cloud.)
REM ============================================================
cd /d "%~dp0"

echo.
echo Staging changes...
git add -A

echo Committing...
git commit -m "Refresh odds %DATE% %TIME%"
if errorlevel 1 (
  echo   Nothing new to publish — files already up to date.
) else (
  echo Pushing to GitHub...
  git push
  echo.
  echo Done. The live site will redeploy in ~1-2 minutes:
  echo   https://techneva.github.io/edge-studio/
)

echo.
pause
