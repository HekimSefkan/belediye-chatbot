"""
Chatbot cevap üretimi.

Eşleştiricinin (matcher) sonucunu vatandaşa gösterilecek cevaba dönüştürür:
- Selamlama / teşekkür mesajlarına kısa hazır cevap
- Eşleşme bulunduysa SSS cevabı + ilgili departman
- Bulunamadıysa yönlendirme mesajı + öneriler + "talep oluşturayım mı?" teklifi
"""

from chatbot.preprocessor import tokenize

GREETING_WORDS = {"merhaba", "merhabalar", "selam", "selamlar", "slm", "gunaydin",
                  "iyi", "gunler", "aksamlar", "hey", "sa", "selamunaleykum"}
THANKS_WORDS = {"tesekkur", "tesekkurler", "tesekkurederim", "sagol", "sagolun",
                "eyvallah", "eyv", "tsk", "tskler", "ederim"}

GREETING_ANSWER = (
    "Merhaba! Ben Mardin Büyükşehir Belediyesi vatandaş hizmetleri asistanıyım. "
    "Su, imar, zabıta, temizlik, nikah, vergi, ulaşım gibi konulardaki sorularınızı "
    "yazabilir veya aşağıdaki hızlı sorulardan birini seçebilirsiniz."
)
THANKS_ANSWER = "Rica ederim! Başka bir konuda yardımcı olabilirsem sormanız yeterli."


def _only_words_from(tokens, word_set):
    """Mesajdaki kelimelerin tamamı verilen kümeden mi? (kısa mesajlar için)"""
    return bool(tokens) and len(tokens) <= 4 and all(t in word_set for t in tokens)


def build_response(message, matcher, routing_threshold, default_department):
    """
    Mesaja verilecek cevabı hazırlar. Dönen sözlük hem API cevabı olarak
    kullanılır hem de chat_log tablosuna kaydedilir.
    """
    tokens = tokenize(message)

    # 1) Selamlama ve teşekkür mesajları (SSS araması yapmaya gerek yok)
    if _only_words_from(tokens, GREETING_WORDS):
        return _simple_reply(GREETING_ANSWER, "greeting")
    if _only_words_from(tokens, THANKS_WORDS | GREETING_WORDS):
        return _simple_reply(THANKS_ANSWER, "thanks")

    # 2) TF-IDF ile en yakın SSS'yi bul
    match = matcher.find_best_match(message)
    faq = match["faq"]

    if match["found"]:
        return {
            "type": "answer",
            "answer": faq["cevap"],
            "found": True,
            "score": match["score"],
            "category": faq["kategori"],
            "department": faq["departman"],
            "matched_question": faq["soru"],
            "suggestions": [],
            "offer_ticket": False,
        }

    # 3) Cevap bulunamadı: en yakın SSS'nin departmanını tahmin et, yoksa genel birime yönlendir
    if faq is not None and match["score"] >= routing_threshold:
        department = faq["departman"]
    else:
        department = default_department

    suggestions = [s["soru"] for s in matcher.suggestions(message, routing_threshold)]

    answer = (
        "Bu konuda net bir cevap bulamadım. "
        f"Sorunuz için sizi {department} birimine yönlendirebilirim. "
        "İsterseniz talebinizi/şikayetinizi kaydedebilirim; ilgili birim sizinle ilgilenecektir. "
        "Talep olarak kaydetmemi ister misiniz?"
    )

    return {
        "type": "not_found",
        "answer": answer,
        "found": False,
        "score": match["score"],
        "category": None,
        "department": department,
        "matched_question": None,
        "suggestions": suggestions,
        "offer_ticket": True,
    }


def _simple_reply(text, reply_type):
    """Selamlama/teşekkür gibi SSS dışı kısa cevaplar için ortak yapı."""
    return {
        "type": reply_type,
        "answer": text,
        "found": True,
        "score": 1.0,
        "category": None,
        "department": None,
        "matched_question": None,
        "suggestions": [],
        "offer_ticket": False,
    }
