@echo off
setlocal
:: Launcher for MSDS Efficiency Workflow using standard Python 3.12+
where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    py -3.12 "%~dp0scripts\run_efficiency_workflow.py" %*
) else (
    python "%~dp0scripts\run_efficiency_workflow.py" %*
)
endlocal
