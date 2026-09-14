@echo off
setlocal
rem ==================================================================
rem  Tum otomatik testleri (pytest) calistirir.
rem  Aktivasyon kullanilmaz; venv icindeki python dogrudan cagrilir.
rem ==================================================================

cd /d "%~dp0"
title Chatbot Testleri
set "PYTHONUTF8=1"

if not exist "venv\Scripts\python.exe" goto :venv_yok

echo Testler calistiriliyor...
echo.
"venv\Scripts\python.exe" -m pytest -v
if errorlevel 1 goto :basarisiz

echo.
echo  TUM TESTLER BASARIYLA GECTI.
pause
exit /b 0

:basarisiz
echo.
echo  [!] Bazi testler basarisiz oldu. Yukaridaki FAILED satirlarina bakin.
pause
exit /b 1

:venv_yok
echo [HATA] Sanal ortam bulunamadi: venv\Scripts\python.exe
echo        Once basla.bat dosyasini calistirin; ilk kurulumu otomatik yapar.
pause
exit /b 1
