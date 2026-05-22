@ECHO OFF
curl -s http://localhost:4141 >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO [ERROR] copilot-api is not running on localhost:4141
    ECHO Please open another terminal and run: copilot-api start
    EXIT /B 1
)
ECHO [OK] copilot-api is running

REM ---------- Model config ----------
set AI_PROVIDER=copilot_api
set ANTHROPIC_BASE_URL=http://localhost:4141
set ANTHROPIC_AUTH_TOKEN=dummy
if not defined COPILOT_API_MODEL set COPILOT_API_MODEL=gpt-4.1

REM ---------- Python resolution ----------
set PYTHON_EXECUTABLE=
for /f "delims=" %%P in ('where python 2^>nul') do (
    if not defined PYTHON_EXECUTABLE (
        echo %%P | findstr /i /v "WindowsApps" >nul && set "PYTHON_EXECUTABLE=%%P"
    )
)
if not defined PYTHON_EXECUTABLE (
    for /f "delims=" %%P in ('where py 2^>nul') do (
        if not defined PYTHON_EXECUTABLE set "PYTHON_EXECUTABLE=%%P"
    )
)
if not defined PYTHON_EXECUTABLE if exist "%USERPROFILE%\AppData\Local\Programs\Python\Python312\python.exe" set "PYTHON_EXECUTABLE=%USERPROFILE%\AppData\Local\Programs\Python\Python312\python.exe"
if not defined PYTHON_EXECUTABLE if exist "%USERPROFILE%\AppData\Local\Programs\Python\Python313\python.exe" set "PYTHON_EXECUTABLE=%USERPROFILE%\AppData\Local\Programs\Python\Python313\python.exe"
if not defined PYTHON_EXECUTABLE (
    for /f "delims=" %%P in ('dir /b /s "%USERPROFILE%\AppData\Local\Programs\Python\Python*\python.exe" 2^>nul') do (
        if not defined PYTHON_EXECUTABLE set "PYTHON_EXECUTABLE=%%P"
    )
)
if not defined PYTHON_EXECUTABLE (
    for /f "delims=" %%P in ('dir /b /s "C:\Program Files\Python*\python.exe" 2^>nul') do (
        if not defined PYTHON_EXECUTABLE set "PYTHON_EXECUTABLE=%%P"
    )
)
if not defined PYTHON_EXECUTABLE (
    ECHO [ERROR] Python was not found. Install Python or add it to PATH.
    EXIT /B 1
)

REM ---------- Launch ----------
ECHO === 3D Agent starting with copilot-api model: %COPILOT_API_MODEL% ===
"%PYTHON_EXECUTABLE%" .\3d_agent\main.py %*
