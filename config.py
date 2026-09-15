"""
Uygulama ayarları.

Tüm ayarlar önce ortam değişkenlerinden (veya proje kökündeki .env dosyasından)
okunur; tanımlı değilse aşağıdaki varsayılan değerler kullanılır.
Böylece şifre gibi hassas bilgiler koda gömülmeden değiştirilebilir.
"""

import os
import secrets
from datetime import timedelta

# python-dotenv kuruluysa .env dosyasındaki değerleri ortam değişkenlerine yükle.
# Kurulu değilse proje yine çalışır, sadece varsayılan değerler kullanılır.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Proje kök klasörünün tam yolu (dosya yollarını buna göre oluşturuyoruz)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Bu bilgisayara özel, GitHub'a yüklenmeyen dosyalar (gizli anahtar gibi) bu klasörde tutulur
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")

# Varsayılan demo şifresi. Kullanılıyorsa konsolda ve admin panelinde uyarı gösterilir.
DEFAULT_ADMIN_PASSWORD = "admin123"

# Herkese açık kaynak kodda/örnek dosyada geçen, bu yüzden GİZLİ SAYILMAYAN değerler.
# .env dosyasına bunlardan biri yazılırsa yok sayılır ve rastgele anahtar kullanılır.
PUBLIC_PLACEHOLDER_KEYS = {
    "buraya-uzun-ve-rastgele-bir-deger-yazin",
    "gelistirme-icin-gizli-anahtar-degistirin",
}


def _env_bool(name, default):
    """Ortam değişkenindeki 'True/False/1/0' gibi metinleri bool değere çevirir."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "evet", "yes", "on")


def _env_number(name, default, cast):
    """Sayısal ortam değişkenini okur; hatalı yazılmışsa anlaşılır bir hata verir."""
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default
    try:
        return cast(value)
    except ValueError:
        raise RuntimeError(
            f".env ayarı hatalı: {name}={value!r} bir sayı olmalı (örnek: {default})."
        ) from None


def load_secret_key():
    """
    Oturum çerezlerini imzalayan gizli anahtarı belirler.

    NEDEN ÖNEMLİ? Flask, admin girişini tarayıcıdaki çereze yazar ve bu anahtarla imzalar.
    Anahtar tahmin edilebilirse (örneğin GitHub'daki kodda yazıyorsa) saldırgan kendi
    çerezini imzalayıp ŞİFRE BİLMEDEN admin paneline girebilir.

    Sıra:
      1) .env'de SECRET_KEY varsa ve herkese açık örnek değer değilse onu kullan.
      2) Yoksa instance/secret_key dosyasındaki anahtarı kullan.
      3) O da yoksa rastgele bir anahtar üret ve bu dosyaya kaydet
         (böylece uygulama yeniden başlatılınca admin oturumu kapanmaz).
    instance/ klasörü .gitignore içindedir, GitHub'a yüklenmez.
    """
    env_key = os.environ.get("SECRET_KEY", "").strip()
    if env_key and env_key not in PUBLIC_PLACEHOLDER_KEYS:
        return env_key

    key_path = os.path.join(INSTANCE_DIR, "secret_key")
    try:
        with open(key_path, encoding="utf-8") as f:
            saved_key = f.read().strip()
        if len(saved_key) >= 32:
            return saved_key
    except OSError:
        pass

    new_key = secrets.token_hex(32)
    try:
        os.makedirs(INSTANCE_DIR, exist_ok=True)
        with open(key_path, "w", encoding="utf-8") as f:
            f.write(new_key)
    except OSError:
        # Dosyaya yazılamazsa anahtar sadece bu çalıştırma için geçerli olur
        pass
    return new_key


class Config:
    """Flask uygulamasının kullandığı ayarlar."""

    # Oturum (session) çerezlerini imzalamak için kullanılan gizli anahtar (bkz. load_secret_key)
    SECRET_KEY = load_secret_key()

    # Oturum çerezi güvenliği
    SESSION_COOKIE_HTTPONLY = True        # JavaScript çereze erişemez
    SESSION_COOKIE_SAMESITE = "Lax"       # Başka sitelerden gelen isteklerde çerez gönderilmez
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)  # Admin oturumu en fazla 8 saat açık kalır

    # İstek gövdesi sınırı: çok büyük istekler belleğe alınmadan reddedilir (413)
    MAX_CONTENT_LENGTH = 64 * 1024  # 64 KB (en uzun talep formu bile ~3 KB)

    # SQLite veritabanı dosyası ve şema/seed dosyalarının yolları
    DATABASE_PATH = os.environ.get(
        "DATABASE_PATH", os.path.join(BASE_DIR, "database", "chatbot.db")
    )
    SCHEMA_PATH = os.path.join(BASE_DIR, "database", "schema.sql")
    SEED_PATH = os.path.join(BASE_DIR, "database", "seed_data.json")

    # Başlangıç admin kullanıcısı (şifre veritabanına hash'lenerek kaydedilir)
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin").strip() or "admin"
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD") or DEFAULT_ADMIN_PASSWORD

    # Admin girişinde deneme sınırı (kaba kuvvet / şifre tahmini saldırısına karşı)
    LOGIN_MAX_ATTEMPTS = 5            # Bu kadar hatalı denemeden sonra...
    LOGIN_LOCK_SECONDS = 5 * 60       # ...bu süre boyunca giriş engellenir

    # Chatbot eşleştirme eşiği: bu skorun altı "cevap bulunamadı" demektir
    SIMILARITY_THRESHOLD = _env_number("SIMILARITY_THRESHOLD", 0.35, float)

    # Eşik altında kalsa bile bu skorun üzerindeyse ("yakın ama emin değil" bandı)
    # en yakın SSS'nin departmanı "muhtemel ilgili birim" olarak önerilir.
    # Daha düşük skorlarda vatandaş genel birime (Beyaz Masa) yönlendirilir.
    ROUTING_THRESHOLD = 0.30

    # Hiçbir birim tahmin edilemezse vatandaşın yönlendirileceği genel birim (demo)
    DEFAULT_DEPARTMENT = "Beyaz Masa (Vatandaş İletişim Merkezi)"

    # Debug modu VARSAYILAN OLARAK KAPALI. Açıkken hata sayfaları kaynak kodu ve dosya
    # yollarını gösterir; sadece geliştirme sırasında .env'de FLASK_DEBUG=True yapılmalı.
    DEBUG = _env_bool("FLASK_DEBUG", False)
    PORT = _env_number("PORT", 5000, int)

    # Test sırasında True yapılır
    TESTING = False
