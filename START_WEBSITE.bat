@echo off
title Content Repurposing Chain - Web Server Launcher
color 0A

echo =========================================================
echo   🚀 STARTING CONTENT REPURPOSING CHAIN WEB APPLICATION
echo   Team 24 | Problem 22 | Marwadi University Hackathon
echo =========================================================
echo.

cd /d "%~dp0"

echo [1/2] Starting Node.js Express Server on Port 3000...
start /b node server.js

timeout /t 2 /nobreak >nul

echo [2/2] Opening Web Browser at http://localhost:3000...
start http://localhost:3000

echo.
echo =========================================================
echo   SUCCESS! Website is running live at http://localhost:3000
echo   Keep this window open while using the website.
echo =========================================================
echo.
pause
