@echo off
REM Run dbt with environment variables from .env file
REM Usage: run_dbt.bat [command]
REM Example: run_dbt.bat build

REM Activate virtual environment
call venv\Scripts\activate

REM Load environment variables from .env file
for /f "tokens=1,2 delims==" %%a in (.env) do (
    set %%a=%%b
)

REM Run dbt with the specified command (default: build)
cd dbt_sdg
if "%1"=="" (
    dbt build --profiles-dir .
) else (
    dbt %* --profiles-dir .
)
