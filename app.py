"""
Mardin Büyükşehir Belediyesi - Vatandaş Hizmetleri Chatbotu
Uygulamanın giriş noktası.

Çalıştırmak için:
    python app.py
Ardından tarayıcıda: http://127.0.0.1:5000

Not: Bu proje bir staj çalışmasıdır; içerdiği veriler kurgusal demo verisidir.
"""

from flask import Flask

from chatbot.matcher import FAQMatcher
from config import Config
from database.db import close_db, connect, fetch_all_faqs, init_db
from routes.admin_routes import admin_bp, generate_csrf_token
from routes.api_routes import api_bp
from routes.chat_routes import chat_bp


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

    return app


if __name__ == "__main__":
    application = create_app()
    print("Chatbot çalışıyor:  http://127.0.0.1:%s" % application.config["PORT"])
    print("Admin paneli:       http://127.0.0.1:%s/admin" % application.config["PORT"])
    application.run(
        host="127.0.0.1",
        port=application.config["PORT"],
        debug=application.config["DEBUG"],
    )
