@echo off
chcp 65001 >nul
setlocal
rem ==================================================================
rem  Tüm otomatik testleri (pytest) çalıştırır.
rem  Aktivasyon kullanılmaz; venv içindeki python doğrudan çağrılır.
rem ==================================================================

cd /d "%~dp0"
title Testler - Belediye Chatbot
set "PYTHONUTF8=1"

if not exist "venv\Scripts\python.exe" goto :venv_yok

echo Testler çalıştırılıyor...
echo.
"venv\Scripts\python.exe" -m pytest -v
if errorlevel 1 goto :basarisiz

echo.
echo  TÜM TESTLER BAŞARIYLA GEÇTİ.
pause
exit /b 0

:basarisiz
echo.
echo  [!] Bazı testler başarısız oldu. Yukarıdaki FAILED satırlarına bakın.
pause
exit /b 1

:venv_yok
echo [HATA] Sanal ortam bulunamadı: venv\Scripts\python.exe
echo        Önce basla.bat dosyasını çalıştırın; ilk kurulumu otomatik yapar.
pause
exit /b 1
