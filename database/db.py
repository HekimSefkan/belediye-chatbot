"""
Veritabanı yardımcı fonksiyonları.

- get_db():   İstek (request) boyunca kullanılacak SQLite bağlantısını verir.
- init_db():  Tabloları oluşturur, SSS tablosu boşsa örnek veriyi yükler,
              admin kullanıcısını config'deki bilgilerle eşitler.

GÜVENLİK NOTU: Bu projedeki tüm SQL sorguları "?" yer tutuculu (parametreli)
yazılmıştır. Kullanıcıdan gelen veri asla SQL metnine string olarak eklenmez;
bu sayede SQL injection saldırıları engellenir.
"""

import json
import os
import sqlite3

from flask import current_app, g
from werkzeug.security import check_password_hash, generate_password_hash


def connect(db_path):
    """Verilen yoldaki SQLite dosyasına bağlanır (dosya yoksa oluşturulur)."""
    folder = os.path.dirname(db_path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    conn = sqlite3.connect(db_path)
    # Satırlara sütun adıyla erişebilmek için: row["soru"]
    conn.row_factory = sqlite3.Row
    return conn


def get_db():
    """
    Aktif istek için veritabanı bağlantısını döndürür.
    Flask'ın 'g' nesnesinde saklanır; aynı istek içinde tekrar tekrar bağlanılmaz.
    """
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE_PATH"])
    return g.db


def close_db(exception=None):
    """İstek bittiğinde bağlantıyı kapatır (app.teardown_appcontext ile çağrılır)."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


class DatabaseSetupError(RuntimeError):
    """Uygulama açılırken veritabanı hazırlanamazsa kullanıcıya gösterilecek anlaşılır hata."""


def init_db(config):
    """
    Uygulama açılırken bir kez çalışır:
    1) schema.sql ile tabloları oluşturur,
    2) faq tablosu boşsa seed_data.json içindeki demo soruları ekler,
    3) admin kullanıcısını oluşturur/şifresini günceller.

    Bir şey ters giderse Python hata çıktısı yerine ne yapılması gerektiğini
    anlatan bir DatabaseSetupError fırlatır.
    """
    try:
        conn = connect(config["DATABASE_PATH"])
    except (sqlite3.Error, OSError) as error:
        raise DatabaseSetupError(
            f"Veritabanı dosyası açılamadı: {config['DATABASE_PATH']} ({error})."
        ) from error

    try:
        try:
            with open(config["SCHEMA_PATH"], encoding="utf-8") as f:
                conn.executescript(f.read())
        except OSError as error:
            raise DatabaseSetupError(
                f"Şema dosyası bulunamadı: {config['SCHEMA_PATH']}. "
                "Proje dosyaları eksik olabilir; depoyu GitHub'dan yeniden indirin."
            ) from error
        except sqlite3.DatabaseError as error:
            raise DatabaseSetupError(
                f"Veritabanı dosyası bozuk görünüyor ({error}). "
                "sifirla.bat ile veritabanını yeniden oluşturabilirsiniz."
            ) from error

        faq_count = conn.execute("SELECT COUNT(*) FROM faq").fetchone()[0]
        if faq_count == 0:
            seed_faqs(conn, config["SEED_PATH"])

        sync_admin_user(conn, config["ADMIN_USERNAME"], config["ADMIN_PASSWORD"])
        conn.commit()
    finally:
        conn.close()


def seed_faqs(conn, seed_path):
    """seed_data.json dosyasındaki örnek SSS kayıtlarını veritabanına ekler."""
    try:
        with open(seed_path, encoding="utf-8") as f:
            data = json.load(f)
        rows = [
            (
                category["kategori"],
                item["soru"],
                item["cevap"],
                item.get("anahtar_kelimeler", ""),
                category["departman"],
            )
            for category in data["kategoriler"]
            for item in category["sorular"]
        ]
    except OSError as error:
        raise DatabaseSetupError(
            f"Demo SSS dosyası bulunamadı: {seed_path}. "
            "Dosyayı GitHub'daki orijinal database/seed_data.json ile geri yükleyin."
        ) from error
    except (ValueError, KeyError, TypeError) as error:
        # ValueError: JSON sözdizimi hatası, KeyError/TypeError: beklenen alanlar eksik
        raise DatabaseSetupError(
            f"Demo SSS dosyası bozuk: {seed_path} ({type(error).__name__}: {error}). "
            "Son yaptığınız değişikliği kontrol edin veya dosyayı GitHub'daki orijinaliyle değiştirin."
        ) from error

    conn.executemany(
        "INSERT INTO faq (kategori, soru, cevap, anahtar_kelimeler, departman) "
        "VALUES (?, ?, ?, ?, ?)",
        rows,
    )


def sync_admin_user(conn, username, password):
    """
    Config'deki admin kullanıcı adı/şifresini veritabanına yansıtır.
    - Kullanıcı yoksa oluşturur.
    - Varsa ve şifre değişmişse (örn. .env'de güncellendiyse) hash'i yeniler.
    - Başka kullanıcı adıyla kalmış eski admin kayıtlarını siler. Aksi halde .env'de
      kullanıcı adı değiştirildiğinde eski "admin / admin123" hesabı açık kalırdı.
    Şifre her zaman werkzeug ile hash'lenir, düz metin olarak saklanmaz.
    """
    conn.execute("DELETE FROM admin WHERE kullanici_adi != ?", (username,))

    row = conn.execute(
        "SELECT id, sifre_hash FROM admin WHERE kullanici_adi = ?", (username,)
    ).fetchone()

    if row is None:
        conn.execute(
            "INSERT INTO admin (kullanici_adi, sifre_hash) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )
    elif not check_password_hash(row["sifre_hash"], password):
        conn.execute(
            "UPDATE admin SET sifre_hash = ? WHERE id = ?",
            (generate_password_hash(password), row["id"]),
        )


def fetch_all_faqs(conn):
    """Eşleştirici (matcher) için tüm SSS kayıtlarını sözlük listesi olarak döndürür."""
    rows = conn.execute(
        "SELECT id, kategori, soru, cevap, anahtar_kelimeler, departman FROM faq ORDER BY id"
    ).fetchall()
    return [dict(row) for row in rows]


def fetch_quick_questions(conn, per_category=4):
    """
    Ana sayfadaki "Hızlı Sorular" bölümü için her kategoriden ilk birkaç soruyu döndürür.
    Sonuç: [{"kategori": "...", "sorular": ["...", "..."]}, ...]
    """
    # id sırasına göre okuyoruz; sözlük ekleme sırasını koruduğu için kategoriler
    # veri setindeki sırayla listelenir (SQLite "İ" harfini alfabetik sıralayamıyor).
    rows = conn.execute("SELECT kategori, soru FROM faq ORDER BY id").fetchall()

    grouped = {}
    for row in rows:
        questions = grouped.setdefault(row["kategori"], [])
        if len(questions) < per_category:
            questions.append(row["soru"])

    return [{"kategori": name, "sorular": items} for name, items in grouped.items()]


def fetch_categories(conn):
    """SSS tablosundaki kategori isimlerinin listesi (tekrarsız, veri setindeki sırayla)."""
    rows = conn.execute(
        "SELECT kategori FROM faq GROUP BY kategori ORDER BY MIN(id)"
    ).fetchall()
    return [row["kategori"] for row in rows]


def fetch_departments(conn, default_department=None):
    """
    Talep formunda seçilebilecek departmanlar.
    SSS'lerdeki departmanlar + genel yönlendirme birimi (Beyaz Masa).
    """
    rows = conn.execute(
        "SELECT departman FROM faq GROUP BY departman ORDER BY MIN(id)"
    ).fetchall()
    departments = [row["departman"] for row in rows]
    if default_department and default_department not in departments:
        departments.append(default_department)
    return departments
