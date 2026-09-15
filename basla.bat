@echo off
chcp 65001 >nul
setlocal
rem ==================================================================
rem  Belediye Chatbot - Belediye Vatandaş Hizmetleri Chatbotu
rem  ÇİFT TIKLAYARAK UYGULAMAYI BAŞLATIR.
rem
rem  - chcp 65001: konsolu UTF-8'e alır, Türkçe karakterler düzgün görünür.
rem  - Sanal ortam aktivasyonu (Activate.ps1) KULLANILMAZ; bu yüzden
rem    PowerShell "running scripts is disabled" hatası oluşmaz.
rem  - venv içindeki python.exe tam yoluyla çalıştırılır; bu yüzden
rem    PATH veya Microsoft Store "python" kısayolu sorun çıkarmaz.
rem  - venv yoksa (örneğin proje GitHub'dan yeni indirildiyse) otomatik
rem    olarak oluşturulur ve paketler yüklenir.
rem ==================================================================

rem Bu dosyanın bulunduğu klasöre geç (başka yerden çalıştırılsa bile)
cd /d "%~dp0"
title Belediye Chatbot
rem Python çıktısının da UTF-8 olması için
set "PYTHONUTF8=1"
set "VENV_PY=%~dp0venv\Scripts\python.exe"

rem 1) Sanal ortam yoksa kur
if not exist "%VENV_PY%" call :kurulum || goto :hata

rem 2) Paketler eksikse yükle (waitress sonradan eklendiği için eski kurulumlar da güncellenir)
"%VENV_PY%" -c "import flask, sklearn, dotenv, waitress" >nul 2>&1
if errorlevel 1 call :paketler || goto :hata

rem 3) Uygulamayı başlat
echo.
echo  ================================================
echo   Belediye Chatbot başlatılıyor...
echo   Ana sayfa    : http://127.0.0.1:5000
echo   Admin paneli : http://127.0.0.1:5000/admin
echo   Kapatmak için bu pencereyi kapatın
echo   veya Ctrl+C tuşlarına basın.
echo  ================================================
echo.

rem Sunucu açıldıktan birkaç saniye sonra tarayıcıyı aç
rem (NO_BROWSER ortam değişkeni tanımlıysa tarayıcı açılmaz)
if not defined NO_BROWSER start "" /min cmd /c "ping -n 4 127.0.0.1 >nul & start "" http://127.0.0.1:5000"

"%VENV_PY%" app.py
if errorlevel 1 goto :hata

echo.
echo  Uygulama kapandı.
pause
exit /b 0


rem ------------------------------------------------------------------
:kurulum
echo Sanal ortam (venv) bulunamadı, ilk kurulum yapılıyor...
set "PY="
set "PYARG="

rem a) Python Launcher (py) var mı?
where py >nul 2>&1 && set "PY=py" && set "PYARG=-3"
if defined PY goto :venv_olustur

rem b) Kullanıcı klasörüne kurulmuş Python var mı?
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" set "PY=%%D\python.exe"
)
if defined PY goto :venv_olustur

rem c) PATH'teki python çalışıyor mu? (Store kısayolu ise hata verir)
python --version >nul 2>&1 && set "PY=python"
if defined PY goto :venv_olustur

echo.
echo [HATA] Python bulunamadı.
echo        https://www.python.org adresinden Python 3.11 veya üstünü kurun.
echo        Kurulumda "Add python.exe to PATH" seçeneğini işaretleyin.
exit /b 1

:venv_olustur
echo Kullanılan Python: %PY% %PYARG%
"%PY%" %PYARG% -m venv venv || exit /b 1

:paketler
echo Gerekli paketler yükleniyor, lütfen bekleyin...
"%VENV_PY%" -m pip install --disable-pip-version-check -r requirements.txt || exit /b 1
exit /b 0


rem ------------------------------------------------------------------
:hata
echo.
echo [HATA] Uygulama başlatılamadı veya hatayla kapandı.
echo        Yukarıdaki mesajı kontrol edin.
echo        5000 portunun kullanımda olduğu yazıyorsa uygulama zaten açık olabilir:
echo        diğer basla.bat penceresini kapatıp tekrar deneyin.
pause
exit /b 1
