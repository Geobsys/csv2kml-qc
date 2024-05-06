@echo off

REM Checking permissions (not necessary on Windows)
REM if not "%1"=="am_admin" (powershell start -verb runas '%0' am_admin & exit /b)

REM Installing Git if necessary
if not exist "%ProgramFiles%\Git\bin\git.exe" (
    echo Installing Git...
    choco install git -y
)

REM Installing Python if necessary
if not exist "%ProgramFiles%\Python310\python.exe" (
    echo Installing Python 3.10...
    choco install python --version=3.10 -y
)

REM Creating the virtual environment
python -m venv venv_csv2kml-qc

REM Enabling the virtual environment
call venv_csv2kml-qc\Scripts\activate

REM Install required Python packages
pip install simplekml pyproj shapely numpy pandas fiona argparse regex gpsdatetime gnsstoolbox


