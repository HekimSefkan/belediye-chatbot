"""
API uç noktaları ve admin paneli testleri (Flask test istemcisi ile).
Çalıştırmak için proje klasöründe:  pytest -v
"""

from database.db import connect
from tests.conftest import TEST_ADMIN_PASSWORD, get_csrf_token


def query_one(app, sql, params=()):
    """Test veritabanında tek satırlık sorgu çalıştırır."""
    conn = connect(app.config["DATABASE_PATH"])
    try:
        return conn.execute(sql, params).fetchone()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# /api/chat
# ---------------------------------------------------------------------------

def test_chat_returns_answer_for_known_question(client):
    response = client.post("/api/chat", json={"message": "Su faturamı nasıl ödeyebilirim?"})
    data = response.get_json()

    assert response.status_code == 200
    assert data["found"] is True
    assert data["type"] == "answer"
    assert data["category"] == "Su ve Kanalizasyon"
    assert data["score"] >= 0.35


def test_chat_is_logged_to_database(app, client):
    client.post("/api/chat", json={"message": "otobüs saatleri"})
    row = query_one(app, "SELECT * FROM chat_log ORDER BY id DESC LIMIT 1")

    assert row["kullanici_mesaji"] == "otobüs saatleri"
    assert row["cevap_bulundu_mu"] == 1
    assert row["kategori"] == "Ulaşım"
    assert row["benzerlik_skoru"] > 0


def test_chat_unknown_question_offers_ticket(app, client):
    response = client.post("/api/chat", json={"message": "futbol maçı kaç kaç bitti"})
    data = response.get_json()

    assert response.status_code == 200
    assert data["found"] is False
    assert data["offer_ticket"] is True
    assert data["department"]
    row = query_one(app, "SELECT cevap_bulundu_mu FROM chat_log ORDER BY id DESC LIMIT 1")
    assert row["cevap_bulundu_mu"] == 0


def test_chat_greeting(client):
    data = client.post("/api/chat", json={"message": "merhaba"}).get_json()
    assert data["type"] == "greeting"


def test_chat_rejects_empty_message(client):
    assert client.post("/api/chat", json={"message": "   "}).status_code == 400
    assert client.post("/api/chat", json={}).status_code == 400
    assert client.post("/api/chat", data="duz metin").status_code == 400


def test_chat_rejects_too_long_message(client):
    assert client.post("/api/chat", json={"message": "a" * 501}).status_code == 400


def test_chat_sql_injection_text_is_stored_safely(app, client):
    """Parametreli sorgu sayesinde SQL komutu gibi görünen metin sadece metin olarak saklanır."""
    malicious = "x'); DROP TABLE faq; --"
    assert client.post("/api/chat", json={"message": malicious}).status_code == 200

    assert query_one(app, "SELECT COUNT(*) AS n FROM faq")["n"] > 0
    row = query_one(app, "SELECT kullanici_mesaji FROM chat_log ORDER BY id DESC LIMIT 1")
    assert row["kullanici_mesaji"] == malicious


# ---------------------------------------------------------------------------
# /api/talep ve yardımcı uçlar
# ---------------------------------------------------------------------------

def test_create_ticket_success(app, client):
    response = client.post("/api/talep", json={
        "ad_soyad": "Test Vatandaş",
        "telefon": "0555 000 00 00",
        "konu": "Sokak lambası yanmıyor",
        "aciklama": "Demo açıklama",
        "departman": "Beyaz Masa (Vatandaş İletişim Merkezi)",
    })
    data = response.get_json()

    assert response.status_code == 201
    assert data["success"] is True
    row = query_one(app, "SELECT * FROM talep_sikayet WHERE id = ?", (data["ticket_id"],))
    assert row["ad_soyad"] == "Test Vatandaş"
    assert row["durum"] == "Beklemede"


def test_create_ticket_validation_errors(client):
    response = client.post("/api/talep", json={"telefon": "abc", "departman": "Olmayan Birim"})
    errors = response.get_json()["errors"]

    assert response.status_code == 400
    assert set(errors) == {"ad_soyad", "konu", "aciklama", "telefon", "departman"}


def test_quick_questions_endpoint(client):
    data = client.get("/api/hizli-sorular").get_json()
    assert len(data) >= 8
    assert data[0]["kategori"] and data[0]["sorular"]


def test_departments_endpoint_includes_default(app, client):
    data = client.get("/api/departmanlar").get_json()
    assert app.config["DEFAULT_DEPARTMENT"] in data


def test_index_page(client):
    response = client.get("/")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Hızlı Sorular" in html
    assert "kurgusal demo verisidir" in html


# ---------------------------------------------------------------------------
# Admin paneli
# ---------------------------------------------------------------------------

def test_admin_pages_require_login(client):
    for url in ["/admin/", "/admin/istatistik", "/admin/sss", "/admin/talepler", "/admin/sohbet-gecmisi"]:
        response = client.get(url)
        assert response.status_code == 302
        assert "/admin/giris" in response.headers["Location"]


def test_admin_password_is_hashed(app):
    row = query_one(app, "SELECT sifre_hash FROM admin WHERE kullanici_adi = 'admin'")
    assert row["sifre_hash"] != TEST_ADMIN_PASSWORD
    assert row["sifre_hash"].startswith(("scrypt:", "pbkdf2:"))


def test_admin_login_wrong_password(client):
    token = get_csrf_token(client)
    response = client.post("/admin/giris", data={
        "csrf_token": token, "kullanici_adi": "admin", "sifre": "yanlis",
    })
    assert response.status_code == 200
    assert "hatalı" in response.get_data(as_text=True)
    with client.session_transaction() as session:
        assert "admin_id" not in session


def test_admin_post_without_csrf_is_rejected(client):
    response = client.post("/admin/giris", data={"kullanici_adi": "admin", "sifre": TEST_ADMIN_PASSWORD})
    assert response.status_code == 400


def test_admin_pages_render_after_login(admin_client):
    client, _ = admin_client
    # Önce istatistiklerde veri olsun
    client.post("/api/chat", json={"message": "otobüs saatleri"})
    client.post("/api/chat", json={"message": "anlamsız bir soru xyz"})

    for url in ["/admin/istatistik", "/admin/sss", "/admin/sss/yeni", "/admin/sss/1/duzenle",
                "/admin/talepler", "/admin/sohbet-gecmisi", "/admin/sohbet-gecmisi?filtre=cevapsiz"]:
        assert client.get(url).status_code == 200, url


def test_admin_faq_create_updates_chatbot(admin_client):
    client, token = admin_client
    new_question = "Belediye hayvan barınağı ziyaret saatleri nedir?"

    before = client.post("/api/chat", json={"message": "hayvan barınağı ziyaret saatleri"}).get_json()
    assert before["matched_question"] != new_question

    response = client.post("/admin/sss/yeni", data={
        "csrf_token": token,
        "kategori": "Park ve Bahçeler",
        "soru": new_question,
        "cevap": "Barınak hafta içi 10:00-16:00 arası ziyarete açıktır. (Demo bilgi)",
        "anahtar_kelimeler": "barınak ziyaret hayvan sahiplenme",
        "departman": "Park ve Bahçeler Dairesi Başkanlığı",
    })
    assert response.status_code == 302

    after = client.post("/api/chat", json={"message": "hayvan barınağı ziyaret saatleri"}).get_json()
    assert after["found"] is True
    assert after["matched_question"] == new_question


def test_admin_faq_delete(app, admin_client):
    client, token = admin_client
    assert client.post("/admin/sss/1/sil", data={"csrf_token": token}).status_code == 302
    assert query_one(app, "SELECT * FROM faq WHERE id = 1") is None


def test_admin_ticket_status_update(app, admin_client):
    client, token = admin_client
    ticket_id = client.post("/api/talep", json={
        "ad_soyad": "Ayşe", "konu": "Test", "aciklama": "Demo",
        "departman": "Zabıta Dairesi Başkanlığı",
    }).get_json()["ticket_id"]

    response = client.post(f"/admin/talepler/{ticket_id}/durum", data={
        "csrf_token": token, "durum": "İşlemde",
    })
    assert response.status_code == 302
    assert query_one(app, "SELECT durum FROM talep_sikayet WHERE id = ?", (ticket_id,))["durum"] == "İşlemde"

    # Listede olmayan durum kabul edilmez
    client.post(f"/admin/talepler/{ticket_id}/durum", data={"csrf_token": token, "durum": "Silindi"})
    assert query_one(app, "SELECT durum FROM talep_sikayet WHERE id = ?", (ticket_id,))["durum"] == "İşlemde"
