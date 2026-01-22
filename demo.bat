@echo off
echo ========================================
echo   WHISK AUTOMATION DEMO
echo   Consistent Characters for Veo 3
echo ========================================
echo.

cd /d "%~dp0"

REM Activate virtual environment
call venv_win\Scripts\activate.bat

REM Clear any existing queue
echo [1/4] Clearing queue...
python run.py clear --all

REM Add demo scenes
echo.
echo [2/4] Adding demo scenes...
python run.py add-scene -s 1 -e env_forest -p "A magical enchanted forest at golden hour, rays of sunlight through ancient trees, mystical atmosphere, cinematic"
python run.py add-scene -s 2 -e env_forest -c char_girl -p "A curious young girl exploring the magical forest, discovering glowing butterflies, sense of wonder, cinematic lighting"
python run.py add-scene -s 3 -e env_room -c char_grandma -p "A warm loving grandmother sitting by a cozy fireplace, knitting with gentle smile, warm interior lighting"
python run.py add-scene -s 4 -e env_room -c "char_girl,char_grandma" -p "Grandmother and granddaughter sharing a tender moment reading a storybook together, warm firelight, emotional connection"

REM Show queue
echo.
echo [3/4] Queue status:
python run.py status

REM Process
echo.
echo [4/4] Starting automation - browser will open...
echo Press Ctrl+C to stop at any time
echo.
python run.py process

echo.
echo ========================================
echo   DEMO COMPLETE!
echo   Images saved to: output\
echo ========================================
pause
