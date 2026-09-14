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

# Telefon: rakam, boşluk, +, -, parantez (örn. "0 (482) 000 00 00")
PHONE_PATTERN = re.compile(r"^[0-9+()\-\s]{7,20}$")


@api_bp.route("/chat", methods=["POST"])
def chat():
    """Vatandaşın mesajını alır, en uygun cevabı bulur ve sohbet geçmişine kaydeder."""
    data = request.get_json(silent=True) or {}
    message = data.get("message", "")

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


@api_bp.route("/talep", methods=["POST"])
def create_ticket():
    """Chatbot içindeki formdan gelen talep/şikayeti doğrulayıp kaydeder."""
    data = request.get_json(silent=True) or {}

    # Tüm alanları metne çevirip baştaki/sondaki boşlukları temizle
    fields = {
        key: str(data.get(key) or "").strip()
        for key in ("ad_soyad", "telefon", "konu", "aciklama", "departman")
    }

    # --- Doğrulama: hataları alan adına göre topla, frontend ilgili alanın altında gösterir ---
    errors = {}
    if not fields["ad_soyad"]:
        errors["ad_soyad"] = "Ad soyad zorunludur."
    if not fields["konu"]:
        errors["konu"] = "Konu zorunludur."
    if not fields["aciklama"]:
        errors["aciklama"] = "Açıklama zorunludur."
    if fields["telefon"] and not PHONE_PATTERN.match(fields["telefon"]):
        errors["telefon"] = "Geçerli bir telefon numarası girin (örn. 0 5xx xxx xx xx)."

    for key, limit in FIELD_LIMITS.items():
        if len(fields[key]) > limit and key not in errors:
            errors[key] = f"En fazla {limit} karakter girilebilir."

    db = get_db()
    departments = fetch_departments(db, current_app.config["DEFAULT_DEPARTMENT"])
    if fields["departman"] not in departments:
        errors["departman"] = "Lütfen listeden bir birim seçin."

    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    # --- Kayıt ---
    cursor = db.execute(
        "INSERT INTO talep_sikayet (ad_soyad, telefon, konu, aciklama, departman) "
        "VALUES (?, ?, ?, ?, ?)",
        (fields["ad_soyad"], fields["telefon"], fields["konu"],
         fields["aciklama"], fields["departman"]),
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
