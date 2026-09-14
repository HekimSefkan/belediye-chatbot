@echo off
setlocal
rem ==================================================================
rem  Mardin Buyuksehir Belediyesi - Vatandas Hizmetleri Chatbotu
rem  CIFT TIKLAYARAK UYGULAMAYI BASLATIR.
rem
rem  - Sanal ortam aktivasyonu (Activate.ps1) KULLANILMAZ; bu yuzden
rem    PowerShell "running scripts is disabled" hatasi olusmaz.
rem  - venv icindeki python.exe tam yoluyla calistirilir; bu yuzden
rem    PATH veya Microsoft Store "python" kisayolu sorun cikarmaz.
rem  - venv yoksa (ornegin proje GitHub'dan yeni indirildiyse) otomatik
rem    olarak olusturulur ve paketler yuklenir.
rem ==================================================================

rem Bu dosyanin bulundugu klasore gec (baska yerden calistirilsa bile)
cd /d "%~dp0"
title Mardin Belediye Chatbot
rem Turkce karakterlerin konsolda sorunsuz yazilmasi icin
set "PYTHONUTF8=1"
set "VENV_PY=%~dp0venv\Scripts\python.exe"

rem 1) Sanal ortam yoksa kur
if not exist "%VENV_PY%" call :kurulum || goto :hata

rem 2) Paketler eksikse yukle
"%VENV_PY%" -c "import flask, sklearn, dotenv" >nul 2>&1
if errorlevel 1 call :paketler || goto :hata

rem 3) Uygulamayi baslat
echo.
echo  ================================================
echo   Chatbot baslatiliyor...
echo   Ana sayfa    : http://127.0.0.1:5000
echo   Admin paneli : http://127.0.0.1:5000/admin
echo   Kapatmak icin bu pencereyi kapatin
echo   veya Ctrl+C tuslarina basin.
echo  ================================================
echo.

rem Sunucu acildiktan birkac saniye sonra tarayiciyi ac
rem (NO_BROWSER ortam degiskeni tanimliysa tarayici acilmaz)
if not defined NO_BROWSER start "" /min cmd /c "ping -n 4 127.0.0.1 >nul & start "" http://127.0.0.1:5000"

"%VENV_PY%" app.py
if errorlevel 1 goto :hata

echo.
echo  Uygulama kapandi.
pause
exit /b 0


rem ------------------------------------------------------------------
:kurulum
echo Sanal ortam (venv) bulunamadi, ilk kurulum yapiliyor...
set "PY="
set "PYARG="

rem a) Python Launcher (py) var mi?
where py >nul 2>&1 && set "PY=py" && set "PYARG=-3"
if defined PY goto :venv_olustur

rem b) Kullanici klasorune kurulmus Python var mi?
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" set "PY=%%D\python.exe"
)
if defined PY goto :venv_olustur

rem c) PATH'teki python calisiyor mu? (Store kisayolu ise hata verir)
python --version >nul 2>&1 && set "PY=python"
if defined PY goto :venv_olustur

echo.
echo [HATA] Python bulunamadi.
echo        https://www.python.org adresinden Python 3.11 veya ustunu kurun.
echo        Kurulumda "Add python.exe to PATH" secenegini isaretleyin.
exit /b 1

:venv_olustur
echo Kullanilan Python: %PY% %PYARG%
"%PY%" %PYARG% -m venv venv || exit /b 1

:paketler
echo Gerekli paketler yukleniyor, lutfen bekleyin...
"%VENV_PY%" -m pip install --disable-pip-version-check -r requirements.txt || exit /b 1
exit /b 0


rem ------------------------------------------------------------------
:hata
echo.
echo [HATA] Uygulama baslatilamadi veya hatayla kapandi.
echo        Yukaridaki mesaji kontrol edin.
echo        "Address already in use" yaziyorsa uygulama zaten acik olabilir:
echo        diger basla.bat penceresini kapatip tekrar deneyin.
pause
exit /b 1
