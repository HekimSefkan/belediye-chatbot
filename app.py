"""
Belediye Chatbot - Belediye Vatandaş Hizmetleri Chatbotu
Uygulamanın giriş noktası.

Çalıştırmak için:
    basla.bat  (veya: venv\\Scripts\\python.exe app.py)
Ardından tarayıcıda: http://127.0.0.1:5000

Not: Bu proje bir staj çalışmasıdır; içerdiği veriler kurgusal demo verisidir.
"""

import sys
from datetime import datetime

from flask import Flask, current_app, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

from chatbot.matcher import FAQMatcher
from config import DEFAULT_ADMIN_PASSWORD, Config
from database.db import DatabaseSetupError, close_db, connect, fetch_all_faqs, init_db
from routes.admin_routes import admin_bp, generate_csrf_token
from routes.api_routes import api_bp
from routes.chat_routes import chat_bp

# API hatalarında vatandaşa gösterilecek Türkçe mesajlar
API_ERROR_MESSAGES = {
    400: "İstek anlaşılamadı. Lütfen tekrar deneyin.",
    404: "İstenen adres bulunamadı.",
    405: "Bu adres bu istek türünü desteklemiyor.",
    413: "Gönderilen veri çok büyük.",
    500: "Sunucuda beklenmeyen bir hata oluştu. Lütfen daha sonra tekrar deneyin.",
}


def create_app(test_config=None):
    """
    Flask uygulamasını oluşturur ve yapılandırır ("application factory" deseni).
    test_config: Testlerde geçici veritabanı gibi ayarları değiştirmek için kullanılır.
    """
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    # Türkçe karakterler JSON cevaplarında "ç" gibi kodlar yerine "ç" olarak görünsün
    app.json.ensure_ascii = False

    # 1) Veritabanını hazırla (tablolar, demo SSS verisi, admin kullanıcısı)
    init_db(app.config)

    # 2) TF-IDF modelini veritabanındaki SSS'lerle bir kez eğit.
    #    Model bellekte tutulur; her mesajda yeniden eğitilmez (hızlı cevap için).
    matcher = FAQMatcher(threshold=app.config["SIMILARITY_THRESHOLD"])
    conn = connect(app.config["DATABASE_PATH"])
    try:
        matcher.fit(fetch_all_faqs(conn))
    finally:
        conn.close()
    app.extensions["faq_matcher"] = matcher

    # 3) Sayfa gruplarını (blueprint) kaydet
    app.register_blueprint(chat_bp)                       # /           -> ana sayfa
    app.register_blueprint(api_bp, url_prefix="/api")     # /api/...    -> JSON uç noktaları
    app.register_blueprint(admin_bp, url_prefix="/admin") # /admin/...  -> yönetim paneli

    # 4) Her istek sonunda veritabanı bağlantısını kapat
    app.teardown_appcontext(close_db)

    # 5) Şablonlarda {{ csrf_token() }} kullanılabilsin (form güvenliği için)
    app.jinja_env.globals["csrf_token"] = generate_csrf_token

    # Tarayıcılar sekme simgesini her zaman /favicon.ico adresinden de ister;
    # dosya static klasöründe durur, bu adres ona yönlendirir (404 hatası oluşmasın diye)
    app.add_url_rule("/favicon.ico", "favicon", serve_favicon)

    # 6) Güvenlik başlıkları ve API hata cevapları
    app.after_request(add_security_headers)
    app.register_error_handler(HTTPException, handle_http_error)
    app.register_error_handler(Exception, handle_unexpected_error)

    return app


def serve_favicon():
    """static/favicon.ico dosyasını /favicon.ico adresinden sunar."""
    return send_from_directory(
        current_app.static_folder, "favicon.ico", mimetype="image/vnd.microsoft.icon"
    )


def log_request(response):
    """
    Her isteği konsola tek satır olarak yazar:  [14:05:31] POST /api/talep 400
    (waitress sunucusu istekleri kendiliğinden yazmadığı için eklenmiştir.)
    """
    print(f"[{datetime.now():%H:%M:%S}] {request.method} {request.path} {response.status_code}",
          flush=True)
    return response


def add_security_headers(response):
    """Her cevaba temel tarayıcı güvenlik başlıklarını ekler."""
    # Tarayıcı dosya türünü tahmin etmeye çalışmasın (ör. metni script sanmasın)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    # Sayfalar başka sitelerin iframe'i içinde açılamasın (tıklama tuzağı / clickjacking)
    response.headers.setdefault("X-Frame-Options", "DENY")
    # Başka sitelere gidilirken adres çubuğundaki bilgiler gönderilmesin
    response.headers.setdefault("Referrer-Policy", "same-origin")
    return response


def _is_api_request():
    return request.path.startswith("/api/")


def handle_http_error(error):
    """
    /api/ adreslerindeki 400/404/405/413 gibi hatalarda HTML yerine JSON döndürür;
    sohbet penceresi bu mesajı vatandaşa gösterebilir. Diğer sayfalar Flask'ın varsayılan
    hata sayfasını kullanır.
    """
    if _is_api_request():
        message = API_ERROR_MESSAGES.get(error.code, error.description)
        return jsonify({"error": message}), error.code
    return error


def handle_unexpected_error(error):
    """Beklenmeyen hatalar: API'de JSON 500 döner, ayrıntı sadece sunucu konsoluna yazılır."""
    if isinstance(error, HTTPException):
        return handle_http_error(error)
    current_app.logger.exception("Beklenmeyen hata: %s", request.path)
    if _is_api_request():
        return jsonify({"error": API_ERROR_MESSAGES[500]}), 500
    return "Sunucuda beklenmeyen bir hata oluştu. Lütfen daha sonra tekrar deneyin.", 500


def print_startup_warnings(app):
    """Demo ayarları kullanılıyorsa konsolda uyarı gösterir."""
    if app.config["ADMIN_PASSWORD"] == DEFAULT_ADMIN_PASSWORD:
        print("UYARI: Varsayılan admin şifresi (admin123) kullanılıyor. "
              "Gerçek kullanımda .env dosyasında ADMIN_PASSWORD değerini değiştirin.")
    if app.config["DEBUG"]:
        print("UYARI: Debug modu açık (FLASK_DEBUG=True). Hata sayfaları kaynak kodu gösterir; "
              "sadece geliştirme sırasında kullanın.")


def run_server(app):
    """
    Uygulamayı yerel bilgisayarda (127.0.0.1) başlatır.

    - Normal kullanımda WAITRESS sunucusu kullanılır. Waitress, Windows'ta sorunsuz çalışan,
      saf Python ile yazılmış tek paketlik bir üretim (WSGI) sunucusudur. Flask'ın kendi
      geliştirme sunucusunun "This is a development server" uyarısı bu yüzden çıkmaz.
    - FLASK_DEBUG=True ise Flask'ın geliştirme sunucusu kullanılır (kod değişince otomatik
      yeniden başlar, hata ayıklama için uygundur).
    """
    host, port = "127.0.0.1", app.config["PORT"]

    if app.config["DEBUG"]:
        app.run(host=host, port=port, debug=True)
        return

    app.after_request(log_request)
    try:
        from waitress import serve
    except ImportError:
        print("UYARI: waitress paketi kurulu değil, Flask geliştirme sunucusu kullanılıyor. "
              "Kurmak için: venv\\Scripts\\python.exe -m pip install -r requirements.txt")
        app.run(host=host, port=port)
        return

    print("Sunucu: waitress (kapatmak için Ctrl+C)")
    serve(app, host=host, port=port, threads=8)


if __name__ == "__main__":
    try:
        application = create_app()
    except DatabaseSetupError as setup_error:
        print(f"\n[HATA] {setup_error}\n")
        sys.exit(1)

    print_startup_warnings(application)
    print("Belediye Chatbot çalışıyor:  http://127.0.0.1:%s" % application.config["PORT"])
    print("Admin paneli:                http://127.0.0.1:%s/admin" % application.config["PORT"])
    try:
        run_server(application)
    except KeyboardInterrupt:
        # Ctrl+C ile kapatınca uzun hata çıktısı yerine kısa bir mesaj göster
        print("\nUygulama kapatıldı.")
    except OSError as server_error:
        print(f"\n[HATA] Sunucu başlatılamadı: {server_error}\n"
              f"{application.config['PORT']} portu başka bir program (ör. açık kalmış başka bir "
              "basla.bat penceresi) tarafından kullanılıyor olabilir.")
        sys.exit(1)
