"""
Admin panelinin uçtan uca kullanım senaryosu.

Bir yöneticinin panelde yaptığı işleri gerçek HTTP istekleriyle, sırasıyla dener:
giriş -> istatistikler -> cevaplanamayan sorudan SSS oluşturma -> düzenleme -> silme
-> talep durumu güncelleme -> çıkış.
"""

import re
from urllib.parse import quote

from tests.conftest import TEST_ADMIN_PASSWORD, TEST_ADMIN_USERNAME, get_csrf_token

UNANSWERED = "sokak lambası yanmıyor"


def ask(client, message):
    return client.post("/api/chat", json={"message": message}).get_json()


def page(response):
    return response.get_data(as_text=True)


def test_admin_full_walkthrough(client):
    # --- 0) Vatandaşlar chatbotu kullanıyor ---
    assert ask(client, "otobüs saatleri")["found"] is True
    assert ask(client, "nikah salonu rezervasyonu")["found"] is True
    assert ask(client, UNANSWERED)["found"] is False

    # --- 1) Giriş yapmadan panele girmeye çalışma -> giriş sayfasına yönlendirme ---
    response = client.get("/admin/sss")
    assert response.status_code == 302
    assert "next=/admin/sss" in response.headers["Location"]

    # --- 2) Yanlış şifre ---
    token = get_csrf_token(client)
    response = client.post("/admin/giris", data={
        "csrf_token": token, "kullanici_adi": TEST_ADMIN_USERNAME, "sifre": "yanlis",
    })
    assert "Kullanıcı adı veya şifre hatalı" in page(response)
    # Kullanıcı adı alanı boşalmıyor
    assert f'name="kullanici_adi" value="{TEST_ADMIN_USERNAME}"' in page(response)

    # --- 3) Doğru şifre -> "next" adresine dönüş ---
    response = client.post("/admin/giris?next=/admin/sss", data={
        "csrf_token": token, "kullanici_adi": TEST_ADMIN_USERNAME, "sifre": TEST_ADMIN_PASSWORD,
    })
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/sss")

    # Girişten sonra oturum yenilendiği için sayfadan yeni CSRF token'ı okunur
    html = page(client.get("/admin/sss"))
    token = re.search(r'name="csrf_token" value="([0-9a-f]+)"', html).group(1)

    # Giriş yapmışken giriş sayfası tekrar açılmaz, panele yönlendirir
    assert client.get("/admin/giris").status_code == 302

    # --- 4) İstatistikler: sayılar, grafik verisi ve cevaplanamayan soru ---
    html = page(client.get("/admin/istatistik"))
    assert "Toplam soru" in html and ">3<" in html
    assert 'id="categoryChart"' in html and 'id="answeredChart"' in html
    assert "chart.umd.min.js" in html
    assert UNANSWERED in html
    create_link = "/admin/sss/yeni?soru=" + quote(UNANSWERED)
    assert create_link.replace("%20", "+") in html or create_link in html

    # --- 5) "SSS olarak ekle" bağlantısı: soru alanı önceden dolu gelir ---
    html = page(client.get("/admin/sss/yeni", query_string={"soru": UNANSWERED}))
    assert f'name="soru" value="{UNANSWERED}"' in html

    # Eksik alanla gönderim -> hata mesajı, kayıt oluşmaz
    html = page(client.post("/admin/sss/yeni", data={"csrf_token": token, "soru": UNANSWERED}))
    # (Jinja tırnak işaretini HTML'de &#39; olarak kodlar)
    assert "&#39;Cevap&#39; alanı boş bırakılamaz." in html

    # Eksiksiz gönderim
    response = client.post("/admin/sss/yeni", data={
        "csrf_token": token,
        "kategori": "Ulaşım",
        "soru": "Sokak lambası yanmıyor, nereye bildirebilirim?",
        "cevap": "Sokak aydınlatma arızaları elektrik dağıtım şirketine bildirilir. (Demo bilgi)",
        "anahtar_kelimeler": "sokak lambası aydınlatma direk ışık yanmıyor",
        "departman": "Ulaşım Dairesi Başkanlığı",
    }, follow_redirects=True)
    assert "Yeni SSS kaydı eklendi" in page(response)

    # Chatbot artık bu soruyu cevaplıyor
    answer = ask(client, UNANSWERED)
    assert answer["found"] is True
    assert answer["matched_question"] == "Sokak lambası yanmıyor, nereye bildirebilirim?"

    # --- 6) Düzenleme ---
    html = page(client.get("/admin/sss", query_string={"q": "Sokak lambası"}))
    faq_id = int(re.search(r"/admin/sss/(\d+)/duzenle", html).group(1))

    response = client.post(f"/admin/sss/{faq_id}/duzenle", data={
        "csrf_token": token,
        "kategori": "Ulaşım",
        "soru": "Sokak lambası yanmıyor, nereye bildirebilirim?",
        "cevap": "GÜNCEL: Arızayı Beyaz Masa'ya bildirebilirsiniz. (Demo bilgi)",
        "anahtar_kelimeler": "sokak lambası aydınlatma direk ışık yanmıyor",
        "departman": "Ulaşım Dairesi Başkanlığı",
    }, follow_redirects=True)
    assert "SSS kaydı güncellendi" in page(response)
    assert ask(client, UNANSWERED)["answer"].startswith("GÜNCEL:")

    # --- 7) Silme ---
    response = client.post(f"/admin/sss/{faq_id}/sil", data={"csrf_token": token}, follow_redirects=True)
    assert f"#{faq_id} numaralı SSS kaydı silindi" in page(response)
    assert ask(client, UNANSWERED)["found"] is False

    # Olmayan kaydı silme -> hata mesajı
    response = client.post("/admin/sss/99999/sil", data={"csrf_token": token}, follow_redirects=True)
    assert "bulunamadı" in page(response)

    # --- 8) Talep durumu güncelleme ---
    ticket_id = client.post("/api/talep", json={
        "ad_soyad": "Demo Vatandaş", "konu": UNANSWERED, "aciklama": "Demo",
        "departman": "Beyaz Masa (Vatandaş İletişim Merkezi)",
    }).get_json()["ticket_id"]

    html = page(client.get("/admin/talepler", query_string={"durum": "Beklemede"}))
    assert "Demo Vatandaş" in html

    for status in ["İşlemde", "Tamamlandı"]:
        response = client.post(f"/admin/talepler/{ticket_id}/durum", data={
            "csrf_token": token, "durum": status, "filtre": "",
        }, follow_redirects=True)
        assert f"durumu &#39;{status}&#39; olarak güncellendi" in page(response)

    assert "Demo Vatandaş" in page(client.get("/admin/talepler", query_string={"durum": "Tamamlandı"}))
    assert "Demo Vatandaş" not in page(client.get("/admin/talepler", query_string={"durum": "Beklemede"}))

    response = client.post("/admin/talepler/99999/durum", data={
        "csrf_token": token, "durum": "İşlemde",
    }, follow_redirects=True)
    assert "talep bulunamadı" in page(response)

    # İstatistik kartı talebi "tamamlandı" olarak sayıyor
    assert "1 tamamlandı" in page(client.get("/admin/istatistik"))

    # --- 9) Sohbet geçmişi: cevaplanamayanlar filtresi ---
    html = page(client.get("/admin/sohbet-gecmisi", query_string={"filtre": "cevapsiz"}))
    assert UNANSWERED in html and "otobüs saatleri" not in html

    # --- 10) Çıkış ---
    response = client.post("/admin/cikis", data={"csrf_token": token}, follow_redirects=True)
    assert "Oturum kapatıldı" in page(response)
    assert client.get("/admin/istatistik").status_code == 302
