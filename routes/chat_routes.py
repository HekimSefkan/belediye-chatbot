"""
Vatandaşın gördüğü ana sayfa.
Sohbet widget'ı ve "Hızlı Sorular" listesi bu sayfada yer alır.
"""

from flask import Blueprint, render_template

from database.db import fetch_quick_questions, get_db

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/")
def index():
    """Ana sayfa: kategori bazlı hızlı sorular sunucu tarafında listelenir."""
    quick_questions = fetch_quick_questions(get_db(), per_category=4)
    faq_count = get_db().execute("SELECT COUNT(*) FROM faq").fetchone()[0]
    return render_template(
        "index.html",
        quick_questions=quick_questions,
        faq_count=faq_count,
    )
