@echo off
chcp 65001 >nul
setlocal
rem ==================================================================
rem  DEMO ÖNCESİ TEMİZ BAŞLANGIÇ
rem  Veritabanını (database\chatbot.db) siler ve 70 demo SSS ile
rem  yeniden oluşturur. Sohbet geçmişi, talepler ve SSS'de yapılan
rem  değişiklikler silinir. Admin şifresi .env ayarından tekrar yazılır.
rem ==================================================================

cd /d "%~dp0"
title Veritabanını Sıfırla - Belediye Chatbot
set "PYTHONUTF8=1"

if not exist "venv\Scripts\python.exe" goto :venv_yok

echo.
echo  Bu işlem TÜM sohbet geçmişini, talepleri ve SSS değişikliklerini SİLER
echo  ve demo verileriyle temiz bir veritabanı oluşturur.
echo  Uygulama açıksa (basla.bat penceresi) önce onu kapatın.
echo.

rem SIFIRLA_ONAY tanımlıysa soru sorulmaz (otomatik kullanım için)
if defined SIFIRLA_ONAY goto :sil
set "CEVAP="
set /p "CEVAP=Devam etmek için E yazıp Enter tuşuna basın: "
if /i not "%CEVAP%"=="E" goto :iptal

:sil
if exist "database\chatbot.db" del /q "database\chatbot.db"
if exist "database\chatbot.db" goto :silinemedi

"venv\Scripts\python.exe" -c "from app import create_app; create_app(); print('Veritabanı yeniden oluşturuldu, demo SSS verileri yüklendi.')"
if errorlevel 1 goto :hata

echo.
echo  Hazır! Şimdi basla.bat ile uygulamayı başlatabilirsiniz.
pause
exit /b 0

:iptal
echo İşlem iptal edildi, hiçbir şey silinmedi.
pause
exit /b 0

:silinemedi
echo.
echo [HATA] Veritabanı dosyası silinemedi; uygulama hâlâ açık olabilir.
echo        basla.bat penceresini kapatıp sifirla.bat dosyasını tekrar çalıştırın.
pause
exit /b 1

:hata
echo.
echo [HATA] Veritabanı oluşturulamadı. Yukarıdaki mesajı kontrol edin.
pause
exit /b 1

:venv_yok
echo [HATA] Sanal ortam bulunamadı. Önce basla.bat dosyasını çalıştırın.
pause
exit /b 1
