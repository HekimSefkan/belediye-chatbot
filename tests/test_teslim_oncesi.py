"""
Teslim öncesi yapılan değişikliklerin testleri:
isim ("Belediye Chatbot"), favicon, talep doğrulama mesajları, aydınlatma notu ve sunucu.
"""

import logging
import os
import re

import pytest

import app as app_module

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Taranmayacak klasörler: sanal ortam, git, önbellekler ve otomatik üretilen dosyalar
SKIP_DIRS = {"venv", ".venv", ".git", "__pycache__", ".pytest_cache", "instance"}
TEXT_EXTENSIONS = {".py", ".md", ".html", ".css", ".js", ".json", ".sql", ".bat", ".txt",
                   ".svg", ".example", ".gitignore", ".gitattributes"}
FORBIDDEN_NAME = re.compile(r"mard[iİıI]n", re.IGNORECASE)


# ---------------------------------------------------------------------------
# İsim
# ---------------------------------------------------------------------------

def _project_text_files():
    for folder, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            ext = os.path.splitext(name)[1] or name
            if ext in TEXT_EXTENSIONS or name.startswith(".env"):
                yield os.path.join(folder, name)


def test_no_file_mentions_old_city_name():
    offenders = []
    for path in _project_text_files():
        with open(path, encoding="utf-8", errors="ignore") as f:
            if FORBIDDEN_NAME.search(f.read()):
                offenders.append(os.path.relpath(path, PROJECT_ROOT))
    # Bu test dosyasının kendisi aranan deseni içerdiği için hariç tutulur
    offenders = [p for p in offenders if not p.endswith("test_teslim_oncesi.py")]
    assert offenders == []


def test_pages_use_belediye_chatbot_name(client):
    index = client.get("/").get_data(as_text=True)
    login = client.get("/admin/giris").get_data(as_text=True)
    assert "<title>Belediye Chatbot" in index
    assert "Belediye Chatbot" in login
    greeting = client.post("/api/chat", json={"message": "merhaba"}).get_json()["answer"]
    assert "Belediye Chatbot" in greeting
    for text in (index, login, greeting):
        assert not FORBIDDEN_NAME.search(text)


# ---------------------------------------------------------------------------
# Favicon
# ---------------------------------------------------------------------------

def test_favicon_ico_is_served(client):
    response = client.get("/favicon.ico")
    assert response.status_code == 200
    assert response.mimetype == "image/vnd.microsoft.icon"
    assert response.data[:4] == b"\x00\x00\x01\x00"  # ICO dosya imzası


def test_favicon_svg_is_served(client):
    response = client.get("/static/favicon.svg")
    assert response.status_code == 200
    assert b"<svg" in response.data


def test_pages_link_the_favicon(admin_client):
    client, _ = admin_client
    for url in ["/", "/admin/giris", "/admin/istatistik"]:
        if url == "/admin/giris":
            html = client.application.test_client().get(url).get_data(as_text=True)
        else:
            html = client.get(url).get_data(as_text=True)
        assert 'rel="icon"' in html and "favicon.svg" in html, url


# ---------------------------------------------------------------------------
# Talep doğrulama: kullanıcıya ve konsola anlaşılır neden
# ---------------------------------------------------------------------------

def test_rejected_ticket_explains_each_field(client):
    response = client.post("/api/talep", json={
        "ad_soyad": "", "telefon": "123", "konu": "", "aciklama": "",
        "departman": "Zabıta Dairesi Başkanlığı",
    })
    errors = response.get_json()["errors"]
    assert response.status_code == 400
    assert errors["ad_soyad"] == "Ad soyad zorunludur."
    assert errors["aciklama"] == "Açıklama zorunludur."
    assert "10-13 rakam" in errors["telefon"] and "boş bırakabilirsiniz" in errors["telefon"]


def test_rejected_ticket_logs_field_names_but_not_values(client, caplog):
    with caplog.at_level(logging.WARNING):
        client.post("/api/talep", json={
            "ad_soyad": "Gizli Kisi Adi", "telefon": "abc", "konu": "k", "aciklama": "a",
            "departman": "Zabıta Dairesi Başkanlığı",
        })
    log = caplog.text
    assert "Talep reddedildi" in log and "telefon" in log
    assert "Gizli Kisi Adi" not in log


def test_phone_with_dots_is_accepted(client):
    response = client.post("/api/talep", json={
        "ad_soyad": "Test", "telefon": "0555.123.45.67", "konu": "k", "aciklama": "a",
        "departman": "Zabıta Dairesi Başkanlığı",
    })
    assert response.status_code == 201


def test_ticket_form_script_has_privacy_note_and_required_marks(client):
    script = client.get("/static/js/chat.js").get_data(as_text=True)
    assert "Aydınlatma notu" in script
    assert "ad soyad, telefon (isteğe bağlı) ve talep metni" in script
    assert "staj demo çalışmasıdır" in script and "gerçek kişisel bilgilerinizi girmeyin" in script
    assert "* işaretli alanların doldurulması zorunludur." in script
    assert "Lütfen işaretli alanları düzeltin" in script


# ---------------------------------------------------------------------------
# Sunucu: waitress ve istek kaydı
# ---------------------------------------------------------------------------

def test_run_server_uses_waitress_when_debug_is_off(app, monkeypatch):
    calls = {}

    def fake_serve(wsgi_app, **kwargs):
        calls["app"], calls["kwargs"] = wsgi_app, kwargs

    monkeypatch.setattr("waitress.serve", fake_serve)
    app.config["DEBUG"] = False
    app_module.run_server(app)

    assert calls["app"] is app
    assert calls["kwargs"]["host"] == "127.0.0.1"
    assert calls["kwargs"]["port"] == app.config["PORT"]


def test_request_log_line_format(app, capsys):
    with app.test_request_context("/api/talep", method="POST"):
        response = app.response_class(status=400)
        app_module.log_request(response)
    line = capsys.readouterr().out.strip()
    assert re.fullmatch(r"\[\d\d:\d\d:\d\d\] POST /api/talep 400", line)


@pytest.mark.parametrize("bat_file", ["basla.bat", "sifirla.bat", "testleri_calistir.bat"])
def test_bat_files_switch_console_to_utf8(bat_file):
    with open(os.path.join(PROJECT_ROOT, bat_file), "rb") as f:
        content = f.read()
    assert not content.startswith(b"\xef\xbb\xbf"), "BOM olmamalı (cmd ilk satırı bozar)"
    assert b"\r\n" in content, "CRLF satır sonu olmalı"
    lines = content.decode("utf-8").splitlines()
    assert lines[0] == "@echo off" and lines[1] == "chcp 65001 >nul"
