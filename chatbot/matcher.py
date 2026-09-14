"""
TF-IDF + Cosine Similarity ile soru eşleştirme modülü.

NASIL ÇALIŞIR?
--------------
1) TF-IDF (Term Frequency - Inverse Document Frequency):
   Her SSS kaydı (soru + anahtar kelimeler) sayılardan oluşan bir vektöre çevrilir.
   - TF : Kelime o soruda ne kadar sık geçiyor?
   - IDF: Kelime tüm sorular arasında ne kadar nadir? Nadir kelimeler ("iskan",
          "nikah") daha ayırt edicidir, bu yüzden daha yüksek ağırlık alır.

2) Cosine Similarity (kosinüs benzerliği):
   Kullanıcının mesajı da aynı şekilde vektöre çevrilir ve her SSS vektörüyle
   arasındaki açının kosinüsü hesaplanır.
   - 1.0 -> tamamen aynı kelimeler
   - 0.0 -> hiç ortak kelime yok

3) En yüksek skoru alan SSS seçilir. Skor eşik değerinin (varsayılan 0.35)
   üzerindeyse cevap "bulundu" kabul edilir.

4) Kapsam dışı kontrolü: Mesajda "elektrik", "doğalgaz" gibi belediyenin görev
   alanı dışındaki bir kelime varsa ve bu kelime eşleşen SSS'de geçmiyorsa,
   skor yüksek olsa bile eşleşme reddedilir.
"""

from flask import current_app
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from chatbot.preprocessor import OUT_OF_SCOPE_STEMS, clean_text


class FAQMatcher:
    """SSS kayıtları üzerinde TF-IDF modeli kurar ve mesajlara en yakın soruyu bulur."""

    def __init__(self, threshold=0.35):
        self.threshold = threshold
        self.faqs = []           # SSS kayıtları (sözlük listesi)
        self.vectorizer = None   # scikit-learn TF-IDF nesnesi
        self.faq_matrix = None   # Tüm SSS'lerin TF-IDF vektörleri (satır = SSS)
        self.faq_words = []      # Her SSS dokümanındaki kelime kökleri (kapsam dışı kontrolü için)

    def fit(self, faqs):
        """
        Modeli verilen SSS listesiyle (yeniden) eğitir.
        Admin panelinden SSS eklendiğinde/silindiğinde tekrar çağrılır.
        """
        self.faqs = list(faqs)

        # Her SSS için "soru + anahtar kelimeler" metnini temizleyerek doküman oluştur
        documents = [
            clean_text(f"{faq['soru']} {faq.get('anahtar_kelimeler') or ''}")
            for faq in self.faqs
        ]
        self.faq_words = [set(doc.split()) for doc in documents]

        # Hiç SSS yoksa veya tüm dokümanlar boşsa model kurulamaz
        if not any(documents):
            self.vectorizer = None
            self.faq_matrix = None
            return

        self.vectorizer = TfidfVectorizer(
            # Ön işlemeyi kendimiz yaptık; burada sadece boşluktan bölüyoruz.
            # Varsayılan desen 1 harfli kelimeleri atar, bu desen hepsini tutar.
            token_pattern=r"(?u)\b\w+\b",
            # Aynı kelime çok tekrar etse bile etkisini logaritmik olarak sınırla
            sublinear_tf=True,
        )
        self.faq_matrix = self.vectorizer.fit_transform(documents)

    def _scores(self, cleaned):
        """
        Temizlenmiş mesajı tüm SSS'lerle karşılaştırır.
        (skor, sss_sıra_no) ikililerini skora göre büyükten küçüğe sıralı döndürür.
        """
        if self.vectorizer is None or not cleaned:
            return []

        message_vector = self.vectorizer.transform([cleaned])
        # scores: her SSS için 0-1 arası benzerlik skoru
        scores = cosine_similarity(message_vector, self.faq_matrix)[0]

        ranked = sorted(enumerate(scores), key=lambda pair: pair[1], reverse=True)
        return [(float(score), index) for index, score in ranked]

    def rank(self, message):
        """(skor, sss) ikililerinden oluşan, skora göre sıralı liste döndürür."""
        return [(score, self.faqs[index]) for score, index in self._scores(clean_text(message))]

    def find_best_match(self, message):
        """
        En iyi eşleşmeyi döndürür:
            {"faq": sss_kaydı veya None, "score": 0.0-1.0,
             "found": True/False, "out_of_scope": True/False}

        out_of_scope=True: Mesajda belediyenin görev alanı dışındaki bir kelime
        (elektrik, doğalgaz, hastane...) var ve bu kelime eşleşen SSS'de geçmiyor.
        """
        cleaned = clean_text(message)
        # Mesajdaki kapsam dışı kelimeler (kök hâlinde)
        out_of_scope_words = set(cleaned.split()) & OUT_OF_SCOPE_STEMS

        ranked = self._scores(cleaned)
        if not ranked or ranked[0][0] <= 0:
            return {"faq": None, "score": 0.0, "found": False,
                    "out_of_scope": bool(out_of_scope_words)}

        best_score, best_index = ranked[0]
        # SSS'nin kendisi bu kelimeyi içeriyorsa (örn. "pasaport") engel yok
        out_of_scope = bool(out_of_scope_words - self.faq_words[best_index])

        return {
            "faq": self.faqs[best_index],
            "score": round(best_score, 4),
            "found": best_score >= self.threshold and not out_of_scope,
            "out_of_scope": out_of_scope,
        }

    def suggestions(self, message, min_score, limit=3):
        """
        Cevap bulunamadığında "Bunu mu demek istediniz?" için
        skoru min_score üzerinde olan en fazla 'limit' adet SSS döndürür.
        """
        return [faq for score, faq in self.rank(message)[:limit] if score >= min_score]


# ---------------------------------------------------------------------------
# Flask uygulaması içinde kullanılan tek (paylaşılan) matcher örneği
# ---------------------------------------------------------------------------

def get_matcher():
    """app.py içinde oluşturulan matcher nesnesini döndürür."""
    return current_app.extensions["faq_matcher"]


def reload_matcher():
    """SSS tablosu değiştiğinde modeli veritabanındaki güncel verilerle yeniden eğitir."""
    # Döngüsel import olmaması için burada import ediyoruz
    from database.db import fetch_all_faqs, get_db

    get_matcher().fit(fetch_all_faqs(get_db()))
