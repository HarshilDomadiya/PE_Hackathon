@echo off
title Content Repurposing Chain - Live Link Launcher
color 0B

echo =========================================================
echo   🌐 CREATING LIVE PUBLIC TUNNEL LINK
echo   Team 24 | Problem 22 | Marwadi University Hackathon
echo =========================================================
echo.

cd /d "%~dp0"

echo Generating Live Public URL for port 3000...
npx localtunnel --port 3000 --local-host 127.0.0.1

pause
