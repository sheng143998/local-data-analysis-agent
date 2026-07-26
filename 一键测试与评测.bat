@echo off
chcp 65001 >nul
cd /d %~dp0
echo ============================================
echo  [1/2] Backend tests (pytest, ~1-2 min)
echo ============================================
.venv\Scripts\python -m pytest backend/tests -q > eval\reports\local_pytest_output.txt 2>&1
type eval\reports\local_pytest_output.txt
echo.
echo ============================================
echo  [2/2] Standard eval - 20 questions with REAL model calls
echo  Requires: PostgreSQL running + model endpoint reachable
echo  Takes roughly 5-15 minutes, please wait...
echo ============================================
.venv\Scripts\python eval\scripts\run_eval.py > eval\reports\local_eval_output.txt 2>&1
type eval\reports\local_eval_output.txt
echo.
echo Done. Key outputs:
echo   eval\reports\local_pytest_output.txt
echo   eval\reports\local_eval_output.txt
echo   eval\reports\latest_eval_report.json
echo.
echo Go back to the Claude session and say "done" - I will read and analyze these files.
pause
