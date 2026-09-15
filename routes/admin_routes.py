"""
Admin (yönetim) paneli.

    /admin/giris                  -> giriş formu
    /admin/cikis                  -> oturumu kapat
    /admin/istatistik             -> özet istatistikler + grafikler
    /admin/sss                    -> SSS listesi (ekle / düzenle / sil)
    /admin/talepler               -> talep/şikayet listesi ve durum güncelleme
    /admin/sohbet-gecmisi         -> chat_log kayıtları (özellikle cevaplanamayanlar)

Güvenlik önlemleri:
- Oturum (session) tabanlı giriş; giriş yapılmadan hiçbir admin sayfası açılmaz.
- Şifre kontrolü werkzeug'un check_password_hash fonksiyonuyla yapılır (hash karşılaştırma).
- Tüm POST formlarında CSRF token kontrolü vardır (başka bir siteden sahte form gönderimini engeller).
- Tüm SQL sorguları parametrelidir.
"""

import secrets
import time
from functools import wraps

from flask import (Blueprint, abort, current_app, flash, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash

from chatbot.matcher import reload_matcher
from config import DEFAULT_ADMIN_PASSWORD
from database.db import fetch_categories, fetch_departments, get_db

admin_bp = Blueprint("admin", __name__)

TICKET_STATUSES = ["Beklemede", "İşlemde", "Tamamlandı"]
FAQ_FIELDS = ("kategori", "soru", "cevap", "anahtar_kelimeler", "departman")

# SSS formu alanları: (ekranda görünen ad, zorunlu mu, en fazla karakter)
# Sınırlar şablondaki maxlength değerleriyle aynıdır; sunucu tarafında da kontrol edilir.
FAQ_FIELD_RULES = {
    "kategori": ("Kategori", True, 100),
    "soru": ("Soru", True, 300),
    "cevap": ("Cevap", True, 3000),
    "anahtar_kelimeler": ("Anahtar kelimeler", False, 500),
    "departman": ("Departman", True, 150),
}


# ---------------------------------------------------------------------------
# Yardımcılar: CSRF koruması ve giriş kontrolü
# ---------------------------------------------------------------------------

def generate_csrf_token():
    """Oturuma özel rastgele bir token üretir; formlara gizli alan olarak eklenir."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


@admin_bp.before_request
def check_csrf():
    """Admin panelindeki her POST isteğinde formdaki token ile oturumdaki token aynı olmalı."""
    if request.method == "POST":
        sent_token = request.form.get("csrf_token", "")
        if not sent_token or not secrets.compare_digest(sent_token, session.get("csrf_token", "")):
            abort(400, description="Geçersiz form isteği (CSRF). Sayfayı yenileyip tekrar deneyin.")


def is_logged_in():
    """
    Oturumda admin var mı VE bu admin veritabanında hâlâ kayıtlı mı?
    (.env'de kullanıcı adı değiştirilip eski hesap silindiyse eski oturum da geçersiz olur.)
    """
    admin_id = session.get("admin_id")
    if admin_id is None:
        return False
    exists = get_db().execute("SELECT 1 FROM admin WHERE id = ?", (admin_id,)).fetchone()
    if exists is None:
        session.clear()
        return False
    return True


def login_required(view):
    """Bu dekoratörü alan sayfalar sadece giriş yapmış admin tarafından görülebilir."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not is_logged_in():
            flash("Bu sayfayı görmek için giriş yapmalısınız.", "warning")
            return redirect(url_for("admin.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@admin_bp.context_processor
def inject_admin_warnings():
    """Admin şablonlarında varsayılan şifre uyarısı gösterebilmek için."""
    return {
        "default_password_in_use": current_app.config["ADMIN_PASSWORD"] == DEFAULT_ADMIN_PASSWORD,
    }


# ---------------------------------------------------------------------------
# Giriş denemesi sınırı (şifre tahmini / kaba kuvvet saldırısına karşı)
# ---------------------------------------------------------------------------
# Hatalı denemeler IP adresine göre bellekte sayılır. Uygulama yeniden başlatılınca sıfırlanır;
# tek sunuculu küçük bir uygulama için yeterli ve anlaşılır bir yöntemdir.

def _login_attempts():
    """{ip: (hatalı_deneme_sayısı, ilk_hatalı_denemenin_zamanı)} sözlüğü."""
    return current_app.extensions.setdefault("login_attempts", {})


def login_locked_seconds(ip):
    """Bu IP için giriş engelliyse kalan saniyeyi, değilse 0 döndürür."""
    count, first_failure = _login_attempts().get(ip, (0, 0))
    lock_seconds = current_app.config["LOGIN_LOCK_SECONDS"]
    elapsed = time.time() - first_failure
    if elapsed >= lock_seconds:
        _login_attempts().pop(ip, None)   # Süre dolduysa sayaç sıfırlanır
        return 0
    if count >= current_app.config["LOGIN_MAX_ATTEMPTS"]:
        return int(lock_seconds - elapsed) + 1
    return 0


def record_failed_login(ip):
    count, first_failure = _login_attempts().get(ip, (0, time.time()))
    _login_attempts()[ip] = (count + 1, first_failure)


# ---------------------------------------------------------------------------
# Giriş / çıkış
# ---------------------------------------------------------------------------

@admin_bp.route("/giris", methods=["GET", "POST"])
def login():
    # Zaten giriş yapılmışsa formu tekrar gösterme
    if is_logged_in():
        return redirect(url_for("admin.dashboard"))

    username = ""
    if request.method == "POST":
        username = request.form.get("kullanici_adi", "").strip()
        password = request.form.get("sifre", "")
        ip = request.remote_addr or "bilinmiyor"

        locked = login_locked_seconds(ip)
        if locked:
            flash(f"Çok fazla hatalı deneme yapıldı. Lütfen {locked // 60 + 1} dakika sonra tekrar deneyin.",
                  "error")
            return render_template("admin/login.html", username=username), 429

        admin = get_db().execute(
            "SELECT id, kullanici_adi, sifre_hash FROM admin WHERE kullanici_adi = ?",
            (username,),
        ).fetchone()

        if admin and check_password_hash(admin["sifre_hash"], password):
            _login_attempts().pop(ip, None)
            # Oturum sabitleme saldırısına karşı eski oturumu temizleyip yenisini başlat
            session.clear()
            session.permanent = True   # PERMANENT_SESSION_LIFETIME (8 saat) sonunda sona erer
            session["admin_id"] = admin["id"]
            session["admin_user"] = admin["kullanici_adi"]
            flash("Hoş geldiniz, giriş başarılı.", "success")

            # Sadece site içi adreslere yönlendir (açık yönlendirme açığını önler)
            next_url = request.args.get("next", "")
            if not next_url.startswith("/admin"):
                next_url = url_for("admin.dashboard")
            return redirect(next_url)

        record_failed_login(ip)
        # Kullanıcı adı mı şifre mi yanlış, bilerek söylemiyoruz
        flash("Kullanıcı adı veya şifre hatalı.", "error")

    # Hatalı girişte kullanıcı adı alanı boşalmasın diye geri gönderiyoruz
    return render_template("admin/login.html", username=username)


@admin_bp.route("/cikis", methods=["POST"])
def logout():
    session.clear()
    flash("Oturum kapatıldı.", "success")
    return redirect(url_for("admin.login"))


@admin_bp.route("/")
@login_required
def dashboard():
    """Panelin açılış sayfası istatistik ekranıdır."""
    return redirect(url_for("admin.statistics"))


# ---------------------------------------------------------------------------
# İstatistikler
# ---------------------------------------------------------------------------

@admin_bp.route("/istatistik")
@login_required
def statistics():
    db = get_db()

    totals = db.execute(
        "SELECT COUNT(*) AS toplam, COALESCE(SUM(cevap_bulundu_mu), 0) AS cevaplanan FROM chat_log"
    ).fetchone()
    total_messages = totals["toplam"]
    answered = totals["cevaplanan"]
    unanswered = total_messages - answered
    unanswered_rate = round(unanswered * 100 / total_messages, 1) if total_messages else 0

    # En çok sorulan kategoriler (sadece cevap bulunan, kategorisi olan mesajlar)
    category_rows = db.execute(
        "SELECT kategori, COUNT(*) AS adet FROM chat_log "
        "WHERE kategori IS NOT NULL GROUP BY kategori ORDER BY adet DESC"
    ).fetchall()

    # Son 7 günün günlük mesaj sayıları
    daily_rows = db.execute(
        "SELECT date(tarih) AS gun, COUNT(*) AS adet FROM chat_log "
        "WHERE date(tarih) >= date('now', 'localtime', '-6 days') "
        "GROUP BY gun ORDER BY gun"
    ).fetchall()

    ticket_rows = db.execute(
        "SELECT durum, COUNT(*) AS adet FROM talep_sikayet GROUP BY durum"
    ).fetchall()
    ticket_counts = {status: 0 for status in TICKET_STATUSES}
    ticket_counts.update({row["durum"]: row["adet"] for row in ticket_rows})

    faq_count = db.execute("SELECT COUNT(*) FROM faq").fetchone()[0]

    recent_unanswered = db.execute(
        "SELECT kullanici_mesaji, benzerlik_skoru, tarih FROM chat_log "
        "WHERE cevap_bulundu_mu = 0 ORDER BY id DESC LIMIT 8"
    ).fetchall()

    # Grafik verileri şablonda JSON'a çevrilip Chart.js'e verilir
    chart_data = {
        "categories": {
            "labels": [row["kategori"] for row in category_rows],
            "values": [row["adet"] for row in category_rows],
        },
        "answered": {"labels": ["Cevaplanan", "Cevaplanamayan"], "values": [answered, unanswered]},
        "daily": {
            "labels": [row["gun"] for row in daily_rows],
            "values": [row["adet"] for row in daily_rows],
        },
    }

    return render_template(
        "admin/istatistik.html",
        total_messages=total_messages,
        answered=answered,
        unanswered=unanswered,
        unanswered_rate=unanswered_rate,
        ticket_counts=ticket_counts,
        ticket_total=sum(ticket_counts.values()),
        faq_count=faq_count,
        recent_unanswered=recent_unanswered,
        chart_data=chart_data,
    )


# ---------------------------------------------------------------------------
# SSS yönetimi (CRUD)
# ---------------------------------------------------------------------------

@admin_bp.route("/sss")
@login_required
def faq_list():
    db = get_db()
    selected_category = request.args.get("kategori", "")
    search = request.args.get("q", "").strip()

    # Filtrelere göre sorguyu parça parça oluşturuyoruz; değerler yine "?" ile veriliyor
    query = "SELECT * FROM faq WHERE 1=1"
    params = []
    if selected_category:
        query += " AND kategori = ?"
        params.append(selected_category)
    if search:
        query += " AND (soru LIKE ? OR cevap LIKE ? OR anahtar_kelimeler LIKE ?)"
        params.extend([f"%{search}%"] * 3)
    query += " ORDER BY id"

    return render_template(
        "admin/sss_liste.html",
        faqs=db.execute(query, params).fetchall(),
        categories=fetch_categories(db),
        selected_category=selected_category,
        search=search,
    )


def _read_faq_form():
    """Formdaki SSS alanlarını okur; zorunlu alan ve uzunluk kontrolü yapar."""
    form = {field: request.form.get(field, "").strip() for field in FAQ_FIELDS}
    errors = []
    for field, (label, required, max_length) in FAQ_FIELD_RULES.items():
        if required and not form[field]:
            errors.append(f"'{label}' alanı boş bırakılamaz.")
        elif len(form[field]) > max_length:
            errors.append(f"'{label}' alanı en fazla {max_length} karakter olabilir.")
    return form, errors


def _faq_form_context(form, mode, faq_id=None):
    db = get_db()
    return {
        "form": form,
        "mode": mode,
        "faq_id": faq_id,
        "categories": fetch_categories(db),
        "departments": fetch_departments(db, current_app.config["DEFAULT_DEPARTMENT"]),
    }


@admin_bp.route("/sss/yeni", methods=["GET", "POST"])
@login_required
def faq_create():
    if request.method == "POST":
        form, errors = _read_faq_form()
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("admin/sss_form.html", **_faq_form_context(form, "create"))

        db = get_db()
        db.execute(
            "INSERT INTO faq (kategori, soru, cevap, anahtar_kelimeler, departman) "
            "VALUES (?, ?, ?, ?, ?)",
            tuple(form[field] for field in FAQ_FIELDS),
        )
        db.commit()
        reload_matcher()  # Yeni soru chatbot tarafından hemen kullanılabilsin
        flash("Yeni SSS kaydı eklendi ve chatbot modeli güncellendi.", "success")
        return redirect(url_for("admin.faq_list"))

    # "Sohbet geçmişi" ekranından gelindiyse soru alanı önceden doldurulur
    form = {field: "" for field in FAQ_FIELDS}
    form["soru"] = request.args.get("soru", "")
    return render_template("admin/sss_form.html", **_faq_form_context(form, "create"))


@admin_bp.route("/sss/<int:faq_id>/duzenle", methods=["GET", "POST"])
@login_required
def faq_edit(faq_id):
    db = get_db()
    faq = db.execute("SELECT * FROM faq WHERE id = ?", (faq_id,)).fetchone()
    if faq is None:
        abort(404)

    if request.method == "POST":
        form, errors = _read_faq_form()
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("admin/sss_form.html", **_faq_form_context(form, "edit", faq_id))

        db.execute(
            "UPDATE faq SET kategori = ?, soru = ?, cevap = ?, anahtar_kelimeler = ?, "
            "departman = ? WHERE id = ?",
            (*[form[field] for field in FAQ_FIELDS], faq_id),
        )
        db.commit()
        reload_matcher()
        flash("SSS kaydı güncellendi.", "success")
        return redirect(url_for("admin.faq_list"))

    return render_template("admin/sss_form.html", **_faq_form_context(dict(faq), "edit", faq_id))


@admin_bp.route("/sss/<int:faq_id>/sil", methods=["POST"])
@login_required
def faq_delete(faq_id):
    db = get_db()
    cursor = db.execute("DELETE FROM faq WHERE id = ?", (faq_id,))
    db.commit()
    # rowcount: silinen satır sayısı (0 ise böyle bir kayıt yoktu)
    if cursor.rowcount == 0:
        flash(f"#{faq_id} numaralı SSS kaydı bulunamadı.", "error")
    else:
        reload_matcher()
        flash(f"#{faq_id} numaralı SSS kaydı silindi.", "success")
    return redirect(url_for("admin.faq_list"))


# ---------------------------------------------------------------------------
# Talep / şikayet yönetimi
# ---------------------------------------------------------------------------

@admin_bp.route("/talepler")
@login_required
def tickets():
    selected_status = request.args.get("durum", "")
    query = "SELECT * FROM talep_sikayet"
    params = []
    if selected_status in TICKET_STATUSES:
        query += " WHERE durum = ?"
        params.append(selected_status)
    query += " ORDER BY id DESC"

    return render_template(
        "admin/talepler.html",
        tickets=get_db().execute(query, params).fetchall(),
        statuses=TICKET_STATUSES,
        selected_status=selected_status,
    )


@admin_bp.route("/talepler/<int:ticket_id>/durum", methods=["POST"])
@login_required
def ticket_update_status(ticket_id):
    new_status = request.form.get("durum", "")
    if new_status not in TICKET_STATUSES:
        flash("Geçersiz durum seçildi.", "error")
    else:
        db = get_db()
        cursor = db.execute(
            "UPDATE talep_sikayet SET durum = ? WHERE id = ?", (new_status, ticket_id)
        )
        db.commit()
        if cursor.rowcount == 0:
            flash(f"#{ticket_id} numaralı talep bulunamadı.", "error")
        else:
            flash(f"#{ticket_id} numaralı talebin durumu '{new_status}' olarak güncellendi.", "success")

    # Filtre seçiliyse aynı filtreli listeye geri dön
    return redirect(url_for("admin.tickets", durum=request.form.get("filtre", "")))


# ---------------------------------------------------------------------------
# Sohbet geçmişi
# ---------------------------------------------------------------------------

@admin_bp.route("/sohbet-gecmisi")
@login_required
def chat_history():
    only_unanswered = request.args.get("filtre") == "cevapsiz"
    query = "SELECT * FROM chat_log"
    if only_unanswered:
        query += " WHERE cevap_bulundu_mu = 0"
    query += " ORDER BY id DESC LIMIT 200"

    return render_template(
        "admin/sohbet_gecmisi.html",
        logs=get_db().execute(query).fetchall(),
        only_unanswered=only_unanswered,
    )
