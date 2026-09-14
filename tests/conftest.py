"""
pytest ortak ayarları (fixture'lar).

Her test, geçici klasörde oluşturulan AYRI bir SQLite veritabanı kullanır.
Böylece testler gerçek database/chatbot.db dosyasını değiştirmez ve birbirini etkilemez.
"""

import os
import sys

import pytest

# Proje kök klasörünü import yoluna ekle (tests/ içinden "app" modülünü bulabilmek için)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402

TEST_ADMIN_USERNAME = "admin"
TEST_ADMIN_PASSWORD = "test-sifre-123"


@pytest.fixture
def app(tmp_path):
    """Geçici veritabanıyla test uygulaması oluşturur."""
    application = create_app({
        "TESTING": True,
        "DATABASE_PATH": str(tmp_path / "test.db"),
        "SECRET_KEY": "test-secret",
        "ADMIN_USERNAME": TEST_ADMIN_USERNAME,
        "ADMIN_PASSWORD": TEST_ADMIN_PASSWORD,
    })
    yield application


@pytest.fixture
def client(app):
    """Tarayıcı gibi istek gönderebilen Flask test istemcisi."""
    return app.test_client()


def get_csrf_token(client):
    """Giriş sayfasını açıp oturuma yazılan CSRF token'ını okur."""
    client.get("/admin/giris")
    with client.session_transaction() as session:
        return session["csrf_token"]


@pytest.fixture
def admin_client(client):
    """Admin olarak giriş yapmış test istemcisi. (client, csrf_token) döndürür."""
    token = get_csrf_token(client)
    response = client.post("/admin/giris", data={
        "csrf_token": token,
        "kullanici_adi": TEST_ADMIN_USERNAME,
        "sifre": TEST_ADMIN_PASSWORD,
    })
    assert response.status_code == 302
    # Giriş sonrası oturum temizlendiği için yeni token al
    with client.session_transaction() as session:
        session["csrf_token"] = token
    return client, token
