@echo off
title CPT Analysis Studio - Installation de l'environnement portable
cd /d "%~dp0"

echo ========================================
echo   CPT Analysis Studio - Setup Portable
echo   (Copie Python + Modele IA)
echo ========================================
echo.
echo ATTENTION : Ce script copie environ 23 Go de donnees.
echo Duree estimee : 10-30 minutes selon votre disque.
echo.
pause

set SRC_ENV=C:\Users\Admin\Desktop\RISKIA\RISKIA\riskIA\environment
set SRC_MODEL=C:\Users\Admin\Desktop\RISKIA\RISKIA\riskIA\models\kibali-final-merged
set DST_ENV=%~dp0python
set DST_MODEL=%~dp0models\kibali-final-merged

:: Copier l'environnement Python
echo [1/2] Copie de l'environnement Python (~8.5 Go)...
if not exist "%DST_ENV%" mkdir "%DST_ENV%"
robocopy "%SRC_ENV%" "%DST_ENV%" /E /NFL /NDL /NJH /NJS /nc /ns /np
echo     Environnement Python copie.

:: Copier le modele IA
echo [2/2] Copie du modele IA Kibali (~14.5 Go)...
if not exist "%DST_MODEL%" mkdir "%DST_MODEL%"
robocopy "%SRC_MODEL%" "%DST_MODEL%" /E /NFL /NDL /NJH /NJS /nc /ns /np
echo     Modele IA copie.

echo.
echo ========================================
echo   Installation terminee !
echo   Lancez "launch.bat" pour demarrer.
echo ========================================
pause
