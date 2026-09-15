"""
Chatbot cevap üretimi.

Eşleştiricinin (matcher) sonucunu vatandaşa gösterilecek cevaba dönüştürür:
- Selamlama / teşekkür mesajlarına kısa hazır cevap
- Eşleşme bulunduysa SSS cevabı + ilgili departman
- Konu belediyenin görev alanı dışındaysa bilgilendirme + talep teklifi
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
    "yazabilir veya aşağıdaki konulardan birini seçebilirsiniz."
)
THANKS_ANSWER = "Rica ederim! Başka bir konuda yardımcı olabilirsem sormanız yeterli."


def make_reply(reply_type, answer, *, found=False, score=0.0, category=None,
               department=None, matched_question=None, suggestions=None, offer_ticket=False):
    """
    Tüm cevap türleri için ortak sözlük yapısı.
    Bu sözlük hem /api/chat cevabı olarak döner hem de chat_log tablosuna kaydedilir.

    reply_type: "greeting" | "thanks" | "answer" | "out_of_scope" | "not_found"
    """
    return {
        "type": reply_type,
        "answer": answer,
        "found": found,
        "score": score,
        "category": category,
        "department": department,
        "matched_question": matched_question,
        "suggestions": suggestions or [],
        "offer_ticket": offer_ticket,
    }


def _only_words_from(tokens, word_set):
    """Mesajdaki kelimelerin tamamı verilen kümeden mi? (kısa mesajlar için)"""
    return bool(tokens) and len(tokens) <= 4 and all(t in word_set for t in tokens)


def build_response(message, matcher, routing_threshold, default_department):
    """Mesaja verilecek cevabı hazırlar."""
    tokens = tokenize(message)

    # 1) Selamlama ve teşekkür mesajları (SSS araması yapmaya gerek yok)
    if _only_words_from(tokens, GREETING_WORDS):
        return make_reply("greeting", GREETING_ANSWER, found=True, score=1.0)
    if _only_words_from(tokens, THANKS_WORDS | GREETING_WORDS):
        return make_reply("thanks", THANKS_ANSWER, found=True, score=1.0)

    # 2) TF-IDF ile en yakın SSS'yi bul
    match = matcher.find_best_match(message)
    faq = match["faq"]

    if match["found"]:
        return make_reply(
            "answer", faq["cevap"], found=True, score=match["score"],
            category=faq["kategori"], department=faq["departman"],
            matched_question=faq["soru"],
        )

    # 3) Konu belediyenin görev alanı dışında (elektrik, doğalgaz, sağlık, eğitim...)
    if match["out_of_scope"]:
        answer = (
            "Bu konu belediyemizin hizmet alanı dışında görünüyor. Elektrik, doğalgaz, sağlık, "
            "eğitim gibi konular ilgili kurum ve şirketlerin sorumluluğundadır. "
            f"Yine de isterseniz sorunuzu {default_department} birimine talep olarak iletebilirim. "
            "Talep olarak kaydetmemi ister misiniz?"
        )
        return make_reply(
            "out_of_scope", answer, score=match["score"],
            department=default_department, offer_ticket=True,
        )

    # 4) Cevap bulunamadı: en yakın SSS'nin departmanını tahmin et, yoksa genel birime yönlendir
    if faq is not None and match["score"] >= routing_threshold:
        department = faq["departman"]
    else:
        department = default_department

    answer = (
        "Bu konuda net bir cevap bulamadım. "
        f"Sorunuz için sizi {department} birimine yönlendirebilirim. "
        "İsterseniz talebinizi/şikayetinizi kaydedebilirim; ilgili birim sizinle ilgilenecektir. "
        "Talep olarak kaydetmemi ister misiniz?"
    )
    return make_reply(
        "not_found", answer, score=match["score"], department=department,
        suggestions=[s["soru"] for s in matcher.suggestions(message, routing_threshold)],
        offer_ticket=True,
    )
