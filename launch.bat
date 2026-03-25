@echo off
title CPT Analysis Studio
cd /d "%~dp0"

echo ========================================
echo   CPT Analysis Studio - RISKIA
echo   Logiciel d'Analyse Geotechnique CPTU
echo ========================================
echo.

:: Verifier que Python portable est present
if not exist "python\python.exe" (
    echo [ERREUR] Python portable non trouve dans python\
    echo Lancez d'abord setup.bat pour installer l'environnement.
    pause
    exit /b 1
)

:: Lancer l'application
echo Demarrage de l'application...
set PYTHONIOENCODING=utf-8
"python\python.exe" run.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERREUR] L'application s'est arretee avec une erreur.
    pause
)
