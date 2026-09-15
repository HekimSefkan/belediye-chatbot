"""
Proje analizinde (docs/proje_analizi.md) bulunan güvenlik açıkları, hata yönetimi
sorunları ve uç durumlar için testler.
"""

import json
import os

import pytest
from flask import Flask
from flask.sessions import SecureCookieSessionInterface

import config as config_module
from app import create_app
from database.db import DatabaseSetupError, connect
from tests.conftest import TEST_ADMIN_PASSWORD, TEST_ADMIN_USERNAME, get_csrf_token

ZABITA = "Zabıta Dairesi Başkanlığı"


def query_all(app, sql, params=()):
    conn = connect(app.config["DATABASE_PATH"])
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def login(client, username=TEST_ADMIN_USERNAME, password=TEST_ADMIN_PASSWORD):
    token = get_csrf_token(client)
    return client.post("/admin/giris", data={
        "csrf_token": token, "kullanici_adi": username, "sifre": password,
    })


def valid_ticket(**overrides):
    data = {"ad_soyad": "Test Vatandaş", "telefon": "", "konu": "Konu",
            "aciklama": "Açıklama", "departman": ZABITA}
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# Gizli anahtar, debug modu, çerez ve başlıklar
# ---------------------------------------------------------------------------

def test_debug_mode_is_off_by_default(monkeypatch):
    monkeypatch.delenv("FLASK_DEBUG", raising=False)
    assert config_module._env_bool("FLASK_DEBUG", False) is False
    if "FLASK_DEBUG" not in os.environ:
        assert config_module.Config.DEBUG is False


def test_secret_key_is_not_a_public_value(app):
    assert app.config["SECRET_KEY"] not in config_module.PUBLIC_PLACEHOLDER_KEYS
    assert len(config_module.Config.SECRET_KEY) >= 32


def test_public_placeholder_secret_key_is_ignored(monkeypatch, tmp_path):
    monkeypatch.setattr(config_module, "INSTANCE_DIR", str(tmp_path))
    monkeypatch.setenv("SECRET_KEY", "buraya-uzun-ve-rastgele-bir-deger-yazin")
    first = config_module.load_secret_key()
    assert first != "buraya-uzun-ve-rastgele-bir-deger-yazin"
    # Üretilen anahtar dosyaya kaydedilir ve sonraki açılışta aynısı kullanılır
    assert (tmp_path / "secret_key").read_text(encoding="utf-8") == first
    assert config_module.load_secret_key() == first


def test_custom_secret_key_from_env_is_used(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "x" * 40)
    assert config_module.load_secret_key() == "x" * 40


def test_session_cookie_signed_with_old_public_key_is_rejected(app):
    """Eski sürümdeki herkese açık anahtarla imzalanmış sahte admin çerezi paneli AÇMAMALI."""
    forger = Flask(__name__)
    forger.secret_key = "gelistirme-icin-gizli-anahtar-degistirin"
    fake_cookie = SecureCookieSessionInterface().get_signing_serializer(forger).dumps(
        {"admin_id": 1, "admin_user": "saldirgan"}
    )
    client = app.test_client()
    client.set_cookie("session", fake_cookie, domain="localhost")
    response = client.get("/admin/istatistik")
    assert response.status_code == 302
    assert "/admin/giris" in response.headers["Location"]


def test_security_headers_are_set(client):
    response = client.get("/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "same-origin"


def test_session_cookie_flags_and_lifetime(client):
    response = login(client)
    cookie = response.headers["Set-Cookie"]
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie
    assert "Expires=" in cookie  # Kalıcı (8 saatlik) oturum


# ---------------------------------------------------------------------------
# Admin hesabı ve giriş denemesi sınırı
# ---------------------------------------------------------------------------

def test_changing_admin_username_removes_old_account(tmp_path):
    db_path = str(tmp_path / "admin.db")
    create_app({"DATABASE_PATH": db_path, "ADMIN_USERNAME": "admin", "ADMIN_PASSWORD": "admin123"})
    new_app = create_app({"DATABASE_PATH": db_path, "ADMIN_USERNAME": "yonetici",
                          "ADMIN_PASSWORD": "Guclu-Sifre-9"})

    assert [row["kullanici_adi"] for row in query_all(new_app, "SELECT kullanici_adi FROM admin")] == ["yonetici"]
    client = new_app.test_client()
    assert login(client, "admin", "admin123").status_code == 200  # giriş başarısız, form tekrar gösterilir
    with client.session_transaction() as session:
        assert "admin_id" not in session


def test_session_of_deleted_admin_is_invalidated(app, client):
    assert login(client).status_code == 302
    conn = connect(app.config["DATABASE_PATH"])
    conn.execute("DELETE FROM admin")
    conn.commit()
    conn.close()
    assert client.get("/admin/istatistik").status_code == 302


def test_login_is_locked_after_too_many_failures(app, client, monkeypatch):
    now = [1_000_000.0]
    monkeypatch.setattr("routes.admin_routes.time.time", lambda: now[0])

    for _ in range(app.config["LOGIN_MAX_ATTEMPTS"]):
        assert login(client, password="yanlis").status_code == 200

    # Sınır aşıldı: doğru şifre bile kabul edilmez
    response = login(client)
    assert response.status_code == 429
    assert "Çok fazla hatalı deneme" in response.get_data(as_text=True)

    # Kilit süresi dolunca doğru şifreyle giriş yapılabilir
    now[0] += app.config["LOGIN_LOCK_SECONDS"] + 1
    assert login(client).status_code == 302


def test_default_password_warning_banner(tmp_path):
    default_app = create_app({"DATABASE_PATH": str(tmp_path / "d.db"), "ADMIN_PASSWORD": "admin123"})
    client = default_app.test_client()
    login(client, "admin", "admin123")
    assert "Varsayılan demo şifresi" in client.get("/admin/istatistik").get_data(as_text=True)


def test_no_warning_banner_with_custom_password(admin_client):
    client, _ = admin_client
    assert "Varsayılan demo şifresi" not in client.get("/admin/istatistik").get_data(as_text=True)


def test_faq_form_rejects_too_long_fields(admin_client):
    client, token = admin_client
    response = client.post("/admin/sss/yeni", data={
        "csrf_token": token, "kategori": "Ulaşım", "soru": "s" * 301, "cevap": "c",
        "departman": "Ulaşım Dairesi Başkanlığı",
    })
    assert "en fazla 300 karakter" in response.get_data(as_text=True)


# ---------------------------------------------------------------------------
# API: bozuk istekler ve uç durumlar 500 hatası vermemeli
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("url", ["/api/chat", "/api/talep"])
@pytest.mark.parametrize("body", ["[1, 2]", '"sadece metin"', "123", "{bozuk json"])
def test_non_object_json_body_returns_400_not_500(client, url, body):
    response = client.post(url, data=body, content_type="application/json")
    assert response.status_code == 400
    assert response.is_json


def test_too_large_request_body_returns_json_413(client):
    response = client.post("/api/chat", json={"message": "a" * 70_000})
    assert response.status_code == 413
    assert "çok büyük" in response.get_json()["error"]


def test_unknown_api_url_returns_json_404(client):
    response = client.get("/api/olmayan-adres")
    assert response.status_code == 404
    assert response.get_json()["error"]


def test_unexpected_error_returns_json_without_traceback(client, monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("gizli iç ayrıntı")

    monkeypatch.setattr("routes.api_routes.build_response", broken)
    response = client.post("/api/chat", json={"message": "otobüs saatleri"})
    assert response.status_code == 500
    body = response.get_data(as_text=True)
    assert "gizli iç ayrıntı" not in body and "Traceback" not in body
    assert response.get_json()["error"]


@pytest.mark.parametrize("message", ["?!.,;:", "😀🙏👍", "how can I pay my water bill", "     x     "])
def test_edge_case_messages_do_not_crash(client, message):
    response = client.post("/api/chat", json={"message": message})
    assert response.status_code == 200
    data = response.get_json()
    assert data["type"] in {"answer", "not_found", "out_of_scope"}
    assert data["answer"]


@pytest.mark.parametrize("phone", ["0555 123 45 67", "+90 555 123 45 67", "0 (850) 000 00 00", "5551234567"])
def test_valid_phone_numbers_are_accepted(client, phone):
    assert client.post("/api/talep", json=valid_ticket(telefon=phone)).status_code == 201


@pytest.mark.parametrize("phone", ["-------", "(((((((((", "12345", "0555-abc-4567", "1" * 14])
def test_invalid_phone_numbers_are_rejected(client, phone):
    response = client.post("/api/talep", json=valid_ticket(telefon=phone))
    assert response.status_code == 400
    assert "telefon" in response.get_json()["errors"]


@pytest.mark.parametrize("field, value", [
    ("ad_soyad", ["x"]), ("konu", 123), ("aciklama", {"a": 1}), ("departman", True),
])
def test_non_string_ticket_fields_are_rejected(client, field, value):
    response = client.post("/api/talep", json=valid_ticket(**{field: value}))
    assert response.status_code == 400
    assert response.get_json()["errors"][field] == "Geçersiz değer."


@pytest.mark.parametrize("field, limit", [("ad_soyad", 100), ("konu", 150), ("aciklama", 2000)])
def test_ticket_field_length_limits(client, field, limit):
    assert client.post("/api/talep", json=valid_ticket(**{field: "a" * limit})).status_code == 201
    response = client.post("/api/talep", json=valid_ticket(**{field: "a" * (limit + 1)}))
    assert response.status_code == 400
    assert f"En fazla {limit}" in response.get_json()["errors"][field]


def test_single_character_name_is_rejected(client):
    response = client.post("/api/talep", json=valid_ticket(ad_soyad="A"))
    assert "ad_soyad" in response.get_json()["errors"]


# ---------------------------------------------------------------------------
# XSS: saldırı metinleri admin sayfalarında kod olarak çalışmamalı
# ---------------------------------------------------------------------------

def test_xss_payloads_are_escaped_in_admin_pages(admin_client):
    client, _ = admin_client
    client.post("/api/chat", json={"message": '<img src=x onerror="alert(1)">'})
    client.post("/api/talep", json=valid_ticket(ad_soyad="<script>alert(2)</script>",
                                                konu='"><svg onload=alert(3)>'))

    for url in ["/admin/talepler", "/admin/sohbet-gecmisi", "/admin/istatistik"]:
        html = client.get(url).get_data(as_text=True)
        assert "<script>alert(2)" not in html
        assert "<img src=x onerror" not in html
        assert "<svg onload" not in html


# ---------------------------------------------------------------------------
# Açılışta anlaşılır hata mesajları
# ---------------------------------------------------------------------------

def test_corrupt_seed_file_gives_clear_error(tmp_path):
    seed = tmp_path / "bozuk.json"
    seed.write_text("{ bozuk json", encoding="utf-8")
    with pytest.raises(DatabaseSetupError, match="Demo SSS dosyası bozuk"):
        create_app({"DATABASE_PATH": str(tmp_path / "a.db"), "SEED_PATH": str(seed)})


def test_seed_file_with_missing_fields_gives_clear_error(tmp_path):
    seed = tmp_path / "eksik.json"
    seed.write_text(json.dumps({"kategoriler": [{"kategori": "X", "sorular": [{"soru": "?"}]}]}),
                    encoding="utf-8")
    with pytest.raises(DatabaseSetupError, match="Demo SSS dosyası bozuk"):
        create_app({"DATABASE_PATH": str(tmp_path / "b.db"), "SEED_PATH": str(seed)})


def test_missing_seed_file_gives_clear_error(tmp_path):
    with pytest.raises(DatabaseSetupError, match="bulunamadı"):
        create_app({"DATABASE_PATH": str(tmp_path / "c.db"), "SEED_PATH": str(tmp_path / "yok.json")})


def test_corrupt_database_file_gives_clear_error(tmp_path):
    db_file = tmp_path / "bozuk.db"
    db_file.write_bytes(b"bu bir sqlite dosyasi degil" * 100)
    with pytest.raises(DatabaseSetupError, match="sifirla.bat"):
        create_app({"DATABASE_PATH": str(db_file)})


def test_invalid_numeric_env_setting_gives_clear_error(monkeypatch):
    monkeypatch.setenv("SIMILARITY_THRESHOLD", "yuzde otuz bes")
    with pytest.raises(RuntimeError, match="SIMILARITY_THRESHOLD"):
        config_module._env_number("SIMILARITY_THRESHOLD", 0.35, float)


# ---------------------------------------------------------------------------
# Model güncellemesi
# ---------------------------------------------------------------------------

def test_matcher_refit_swaps_model_in_one_step(app):
    matcher = app.extensions["faq_matcher"]
    old_model = matcher.model
    old_count = len(old_model.faqs)

    matcher.fit(old_model.faqs[:5])

    assert matcher.model is not old_model
    assert len(matcher.model.faqs) == 5
    # Eski model nesnesi değişmedi: o sırada onu kullanan istek tutarlı veriyle biter
    assert len(old_model.faqs) == old_count
    assert old_model.matrix.shape[0] == old_count
