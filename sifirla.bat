@echo off
setlocal
rem ==================================================================
rem  DEMO ONCESI TEMIZ BASLANGIC
rem  Veritabanini (database\chatbot.db) siler ve 70 demo SSS ile
rem  yeniden olusturur. Sohbet gecmisi, talepler ve SSS'de yapilan
rem  degisiklikler silinir. Admin sifresi .env ayarindan tekrar yazilir.
rem ==================================================================

cd /d "%~dp0"
title Veritabanini Sifirla
set "PYTHONUTF8=1"

if not exist "venv\Scripts\python.exe" goto :venv_yok

echo.
echo  Bu islem TUM sohbet gecmisini, talepleri ve SSS degisikliklerini SILER
echo  ve demo verileriyle temiz bir veritabani olusturur.
echo  Uygulama aciksa (basla.bat penceresi) once onu kapatin.
echo.

rem SIFIRLA_ONAY tanimliysa soru sorulmaz (otomatik kullanim icin)
if defined SIFIRLA_ONAY goto :sil
set "CEVAP="
set /p "CEVAP=Devam etmek icin E yazip Enter tusuna basin: "
if /i not "%CEVAP%"=="E" goto :iptal

:sil
if exist "database\chatbot.db" del /q "database\chatbot.db"
if exist "database\chatbot.db" goto :silinemedi

"venv\Scripts\python.exe" -c "from app import create_app; create_app(); print('Veritabani yeniden olusturuldu, demo SSS verileri yuklendi.')"
if errorlevel 1 goto :hata

echo.
echo  Hazir! Simdi basla.bat ile uygulamayi baslatabilirsiniz.
pause
exit /b 0

:iptal
echo Islem iptal edildi, hicbir sey silinmedi.
pause
exit /b 0

:silinemedi
echo.
echo [HATA] Veritabani dosyasi silinemedi; uygulama hala acik olabilir.
echo        basla.bat penceresini kapatip sifirla.bat dosyasini tekrar calistirin.
pause
exit /b 1

:hata
echo.
echo [HATA] Veritabani olusturulamadi. Yukaridaki mesaji kontrol edin.
pause
exit /b 1

:venv_yok
echo [HATA] Sanal ortam bulunamadi. Once basla.bat dosyasini calistirin.
pause
exit /b 1
