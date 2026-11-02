@echo off
cd /d "%~dp0"
py build_network.py "bc_adaptation_network_input 1.0.xlsx" --screening "bc_adaptation_outcome_screen 2.0.xlsx" --policies "bc_policy_failures_and_enablers.xlsx" --research "research_projects.csv" -o index.html
if errorlevel 1 (
  echo Build failed. Review the error above.
) else (
  echo Open index.html to view the updated map.
)
pause
