"""
Uygulama ayarları.

Tüm ayarlar önce ortam değişkenlerinden (veya proje kökündeki .env dosyasından)
okunur; tanımlı değilse aşağıdaki varsayılan değerler kullanılır.
Böylece şifre gibi hassas bilgiler koda gömülmeden değiştirilebilir.
"""

import os

# python-dotenv kuruluysa .env dosyasındaki değerleri ortam değişkenlerine yükle.
# Kurulu değilse proje yine çalışır, sadece varsayılan değerler kullanılır.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Proje kök klasörünün tam yolu (dosya yollarını buna göre oluşturuyoruz)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _env_bool(name, default):
    """Ortam değişkenindeki 'True/False/1/0' gibi metinleri bool değere çevirir."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "evet", "yes", "on")


class Config:
    """Flask uygulamasının kullandığı ayarlar."""

    # Oturum (session) çerezlerini imzalamak için kullanılan gizli anahtar
    SECRET_KEY = os.environ.get("SECRET_KEY", "gelistirme-icin-gizli-anahtar-degistirin")

    # SQLite veritabanı dosyası ve şema/seed dosyalarının yolları
    DATABASE_PATH = os.environ.get(
        "DATABASE_PATH", os.path.join(BASE_DIR, "database", "chatbot.db")
    )
    SCHEMA_PATH = os.path.join(BASE_DIR, "database", "schema.sql")
    SEED_PATH = os.path.join(BASE_DIR, "database", "seed_data.json")

    # Başlangıç admin kullanıcısı (şifre veritabanına hash'lenerek kaydedilir)
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

    # Chatbot eşleştirme eşiği: bu skorun altı "cevap bulunamadı" demektir
    SIMILARITY_THRESHOLD = float(os.environ.get("SIMILARITY_THRESHOLD", "0.35"))

    # Eşik altında kalsa bile bu skorun üzerindeyse ("yakın ama emin değil" bandı)
    # en yakın SSS'nin departmanı "muhtemel ilgili birim" olarak önerilir.
    # Daha düşük skorlarda vatandaş genel birime (Beyaz Masa) yönlendirilir.
    ROUTING_THRESHOLD = 0.30

    # Hiçbir birim tahmin edilemezse vatandaşın yönlendirileceği genel birim (demo)
    DEFAULT_DEPARTMENT = "Beyaz Masa (Vatandaş İletişim Merkezi)"

    DEBUG = _env_bool("FLASK_DEBUG", True)
    PORT = int(os.environ.get("PORT", "5000"))

    # Test sırasında True yapılır
    TESTING = False
