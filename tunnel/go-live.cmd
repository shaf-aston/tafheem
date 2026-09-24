@echo off
setlocal

:: The only two knobs. The backend's port, and the address it is served on.
set PORT=8000
set TARGET=http://localhost:%PORT%

title Tafheem: live

echo.
echo   Checking the backend is running on port %PORT% ...
curl -s -o nul -w "" %TARGET%/api/health
if errorlevel 1 (
  echo.
  echo   The backend is not running, so there is nothing to put online.
  echo   Start it first, then run this again.
  echo.
  pause
  exit /b 1
)
echo   Found it.
echo.
echo   Opening the tunnel. The address appears below in a few seconds.
echo   Close this window to take the site offline again.
echo.

"%~dp0cloudflared.exe" tunnel --url %TARGET%

endlocal
