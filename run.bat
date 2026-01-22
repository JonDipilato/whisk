@echo off
REM Whisk Automation - Windows Launcher
REM Run directly on Windows for best Chrome compatibility

cd /d "%~dp0"

REM Check if venv exists, if not create it
if not exist "venv_win" (
    echo Creating Windows virtual environment...
    py -m venv venv_win
    echo Installing dependencies...
    call venv_win\Scripts\activate.bat
    pip install -q selenium webdriver-manager rich pandas pydantic click
    echo.
    echo Setup complete!
)

REM Activate venv
call venv_win\Scripts\activate.bat

REM Run the script with all arguments passed through
py run.py %*
