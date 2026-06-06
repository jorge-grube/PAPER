@echo off
cd /d "C:\Users\jorge\OneDrive - UFV\BAINF\PAPER"
echo === Deleting stale index.lock ===
del /f ".git\index.lock" 2>nul
echo === Running git add . ===
git add .
echo === Checking status ===
git status --short
echo === Committing ===
git commit -m "v7 submission-ready manuscript with full pipeline and data"
echo === Pushing ===
git push origin HEAD
echo === Done ===
pause
