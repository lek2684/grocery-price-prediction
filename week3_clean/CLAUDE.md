# Claude Code Startup Instructions

You are working on the Grocery Price Prediction AutoResearch project.

Always read and follow @program.md before doing anything else.

The user should not need to restate the full loop instructions. Treat program.md as the rulebook.

Default behavior:
- Run exactly 5 autonomous iterations.
- Do not ask the user what to try next.
- Do not ask for approval between iterations.
- Only edit model.py.
- Never edit prepare.py, run.py, train.csv, test.csv, or results.tsv manually.
- Run experiments only through python run.py "<description>".
- Keep improvements and revert failures.
- Stop after the requested block and print the Week 5 summary.
