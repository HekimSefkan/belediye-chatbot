"""
JSON API uç noktaları (sohbet penceresindeki JavaScript bu adreslerle konuşur).

    POST /api/chat           -> mesajı eşleştir, cevap dön, chat_log'a kaydet
    POST /api/talep          -> talep/şikayet kaydı oluştur
    GET  /api/hizli-sorular  -> kategori bazlı hızlı soru listesi
    GET  /api/departmanlar   -> talep formundaki departman listesi
"""

import re

from flask import Blueprint, current_app, jsonify, request

from chatbot.matcher import get_matcher
from chatbot.responses import build_response
from database.db import fetch_departments, fetch_quick_questions, get_db

api_bp = Blueprint("api", __name__)

# Kötüye kullanımı önlemek için mesaj ve form alanlarına uzunluk sınırları
MAX_MESSAGE_LENGTH = 500
FIELD_LIMITS = {"ad_soyad": 100, "telefon": 20, "konu": 150, "aciklama": 2000}
TICKET_FIELDS = ("ad_soyad", "telefon", "konu", "aciklama", "departman")

# Telefon: sadece rakam, boşluk, +, -, nokta, parantez (örn. "0 (850) 000 00 00", "0555.123.45.67")
PHONE_PATTERN = re.compile(r"^[0-9+().\-\s]+$")
# Türkiye'deki numaralar 10 (5xx...) ile 12 (+90 5xx...) rakam arasındadır; biraz pay bırakıyoruz
PHONE_MIN_DIGITS, PHONE_MAX_DIGITS = 10, 13


def read_json_object():
    """
    İstek gövdesini JSON nesnesi (sözlük) olarak okur.
    Gövde boş, bozuk ya da nesne yerine liste/metin ise boş sözlük döner;
    böylece sonraki .get() çağrıları 500 hatasına yol açmaz.
    """
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def validate_phone(phone):
    """Telefon boşsa geçerlidir; doluysa izin verilen karakterler ve rakam sayısı kontrol edilir."""
    if not phone:
        return True
    digit_count = sum(ch.isdigit() for ch in phone)
    return bool(PHONE_PATTERN.match(phone)) and PHONE_MIN_DIGITS <= digit_count <= PHONE_MAX_DIGITS


@api_bp.route("/chat", methods=["POST"])
def chat():
    """Vatandaşın mesajını alır, en uygun cevabı bulur ve sohbet geçmişine kaydeder."""
    message = read_json_object().get("message", "")

    # --- Girdi doğrulama ---
    if not isinstance(message, str) or not message.strip():
        return jsonify({"error": "Lütfen bir mesaj yazın."}), 400
    message = message.strip()
    if len(message) > MAX_MESSAGE_LENGTH:
        return jsonify({"error": f"Mesaj en fazla {MAX_MESSAGE_LENGTH} karakter olabilir."}), 400

    # --- Eşleştirme ve cevap üretimi ---
    result = build_response(
        message,
        get_matcher(),
        routing_threshold=current_app.config["ROUTING_THRESHOLD"],
        default_department=current_app.config["DEFAULT_DEPARTMENT"],
    )

    # --- Sohbet geçmişine kaydet (parametreli sorgu -> SQL injection yok) ---
    db = get_db()
    db.execute(
        "INSERT INTO chat_log (kullanici_mesaji, bot_cevabi, benzerlik_skoru, "
        "cevap_bulundu_mu, kategori) VALUES (?, ?, ?, ?, ?)",
        (message, result["answer"], result["score"], int(result["found"]), result["category"]),
    )
    db.commit()

    return jsonify(result)


def validate_ticket(data, departments):
    """
    Talep formu alanlarını temizler ve doğrular.
    (temizlenmiş_alanlar, hatalar) döndürür; hatalar alan adına göre sözlüktür.
    """
    fields, errors = {}, {}

    for key in TICKET_FIELDS:
        value = data.get(key)
        if value is None:
            value = ""
        if not isinstance(value, str):
            # Örn. ad_soyad olarak liste/sayı gönderilmişse metne çevirip kabul etmiyoruz
            errors[key] = "Geçersiz değer."
            value = ""
        fields[key] = value.strip()

    if "ad_soyad" not in errors:
        if not fields["ad_soyad"]:
            errors["ad_soyad"] = "Ad soyad zorunludur."
        elif len(fields["ad_soyad"]) < 2:
            errors["ad_soyad"] = "Ad soyad en az 2 karakter olmalıdır."
    if "konu" not in errors and not fields["konu"]:
        errors["konu"] = "Konu zorunludur."
    if "aciklama" not in errors and not fields["aciklama"]:
        errors["aciklama"] = "Açıklama zorunludur."
    if "telefon" not in errors and not validate_phone(fields["telefon"]):
        errors["telefon"] = (
            "Telefon numarası 10-13 rakamdan oluşmalı ve sadece rakam, boşluk, +, -, nokta "
            "veya parantez içermelidir (örn. 0555 123 45 67). Telefon zorunlu değildir, boş bırakabilirsiniz."
        )

    for key, limit in FIELD_LIMITS.items():
        if len(fields[key]) > limit and key not in errors:
            errors[key] = f"En fazla {limit} karakter girilebilir."

    if "departman" not in errors and fields["departman"] not in departments:
        errors["departman"] = "Lütfen listeden bir birim seçin."

    return fields, errors


@api_bp.route("/talep", methods=["POST"])
def create_ticket():
    """Chatbot içindeki formdan gelen talep/şikayeti doğrulayıp kaydeder."""
    db = get_db()
    departments = fetch_departments(db, current_app.config["DEFAULT_DEPARTMENT"])
    fields, errors = validate_ticket(read_json_object(), departments)

    if errors:
        # Konsolda 400 satırının nedeni görülebilsin diye sadece ALAN ADLARI yazılır
        # (kişisel veri içeren alan değerleri kayda geçirilmez)
        current_app.logger.warning("Talep reddedildi, hatalı alanlar: %s", ", ".join(sorted(errors)))
        return jsonify({"success": False, "errors": errors}), 400

    cursor = db.execute(
        "INSERT INTO talep_sikayet (ad_soyad, telefon, konu, aciklama, departman) "
        "VALUES (?, ?, ?, ?, ?)",
        tuple(fields[key] for key in TICKET_FIELDS),
    )
    db.commit()
    ticket_id = cursor.lastrowid

    return jsonify({
        "success": True,
        "ticket_id": ticket_id,
        "message": (
            f"Talebiniz #{ticket_id} numarasıyla {fields['departman']} birimine iletildi. "
            "Durumunu bu numarayla Beyaz Masa'ya sorabilirsiniz."
        ),
    }), 201


@api_bp.route("/hizli-sorular", methods=["GET"])
def quick_questions():
    """Sohbet penceresindeki kategori butonları için hızlı sorular."""
    return jsonify(fetch_quick_questions(get_db(), per_category=5))


@api_bp.route("/departmanlar", methods=["GET"])
def departments():
    """Talep formundaki 'İlgili birim' açılır listesi için departmanlar."""
    return jsonify(fetch_departments(get_db(), current_app.config["DEFAULT_DEPARTMENT"]))
