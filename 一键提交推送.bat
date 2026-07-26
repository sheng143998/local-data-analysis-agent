@echo off
cd /d %~dp0
echo ============================================
echo  Step 1/3: staging all changes
echo ============================================
git add -A
git status --short
echo.
echo ============================================
echo  Step 2/3: committing
echo ============================================
git commit -F commit_message.txt
if errorlevel 1 (
  echo.
  echo Nothing to commit, or commit failed - see message above.
)
echo.
echo ============================================
echo  Step 3/3: pushing to origin main
echo ============================================
git push origin main
if errorlevel 1 (
  echo.
  echo PUSH FAILED - if a GitHub login window appeared, sign in and run this file again.
) else (
  echo.
  echo PUSH COMPLETE - you can close this window.
)
pause
