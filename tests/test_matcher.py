"""
Metin ön işleme ve TF-IDF eşleştirme testleri.
Çalıştırmak için proje klasöründe:  pytest -v
"""

import json
import os

import pytest

from chatbot.matcher import FAQMatcher
from chatbot.preprocessor import clean_text, normalize_text, turkish_lower
from chatbot.responses import build_response

SEED_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "seed_data.json")


@pytest.fixture(scope="module")
def faqs():
    """seed_data.json dosyasındaki demo SSS'leri düz liste olarak yükler."""
    with open(SEED_PATH, encoding="utf-8") as f:
        data = json.load(f)
    items = []
    for category in data["kategoriler"]:
        for question in category["sorular"]:
            items.append({
                "kategori": category["kategori"],
                "departman": category["departman"],
                "soru": question["soru"],
                "cevap": question["cevap"],
                "anahtar_kelimeler": question.get("anahtar_kelimeler", ""),
            })
    return items


@pytest.fixture(scope="module")
def matcher(faqs):
    m = FAQMatcher(threshold=0.35)
    m.fit(faqs)
    return m


# ---------------------------------------------------------------------------
# Ön işleme (preprocessor)
# ---------------------------------------------------------------------------

def test_turkish_lower_handles_dotted_and_dotless_i():
    assert turkish_lower("İMAR IŞIK") == "imar ışık"


def test_normalize_removes_turkish_chars_and_punctuation():
    assert normalize_text("Çöpler, NE ZAMAN toplanıyor?!") == "copler ne zaman toplaniyor"


def test_clean_text_removes_stopwords_and_stems():
    # "nasıl" stopword olarak atılır, kelimeler ilk 5 harfe indirilir
    assert clean_text("Su faturamı nasıl ödeyebilirim?") == "su fatur odeye"


def test_clean_text_same_root_for_different_suffixes():
    assert clean_text("faturamı") == clean_text("faturası") == clean_text("faturayı")


def test_clean_text_empty_input():
    assert clean_text("") == ""
    assert clean_text("?!.,") == ""


# ---------------------------------------------------------------------------
# Eşleştirme (matcher)
# ---------------------------------------------------------------------------

def test_seed_data_size(faqs):
    """Proje gereksinimi: 8-10 kategori, 60-80 soru."""
    categories = {faq["kategori"] for faq in faqs}
    assert 8 <= len(categories) <= 10
    assert 60 <= len(faqs) <= 80


def test_exact_question_matches_itself(matcher, faqs):
    for faq in faqs:
        result = matcher.find_best_match(faq["soru"])
        assert result["found"], faq["soru"]
        assert result["faq"]["soru"] == faq["soru"]


@pytest.mark.parametrize("message, expected_category", [
    ("su faturası nasıl ödenir", "Su ve Kanalizasyon"),
    ("faturami nerden oderim", "Su ve Kanalizasyon"),          # Türkçe karaktersiz yazım
    ("imar durumu belgesi almak istiyorum", "İmar ve Şehircilik"),
    ("dükkan açmak için ruhsat", "Zabıta"),
    ("cop toplama gunleri", "Temizlik İşleri"),
    ("parktaki salıncak kırılmış", "Park ve Bahçeler"),
    ("evlenmek için gerekli belgeler", "Evlilik/Nikah İşlemleri"),
    ("emlak vergisi son ödeme tarihi", "Emlak/Vergi"),
    ("otobüste çantamı unuttum", "Ulaşım"),
    ("sosyal yardım başvurusu", "Kültür ve Sosyal İşler"),
    ("e-belediye şifremi unuttum", "Bilgi İşlem/BİMER"),
])
def test_paraphrased_questions_match_correct_category(matcher, message, expected_category):
    result = matcher.find_best_match(message)
    assert result["found"] is True
    assert result["score"] >= 0.35
    assert result["faq"]["kategori"] == expected_category


@pytest.mark.parametrize("message", [
    "futbol maçı kaç kaç bitti",
    "pizza siparişi vermek istiyorum",
    "asdfgh qwerty",
])
def test_unrelated_messages_are_below_threshold(matcher, message):
    result = matcher.find_best_match(message)
    assert result["found"] is False
    assert result["score"] < 0.35


def test_only_stopwords_returns_not_found(matcher):
    result = matcher.find_best_match("ve ile mi nasıl")
    assert result == {"faq": None, "score": 0.0, "found": False, "out_of_scope": False}


@pytest.mark.parametrize("message", [
    "hava durumu nasıl olacak",      # önceden "imar durum belgesi" ile eşleşiyordu
    "bugün günlerden ne",            # önceden "çöp toplama günleri" ile eşleşiyordu
])
def test_generic_words_no_longer_cause_false_match(matcher, message):
    assert matcher.find_best_match(message)["found"] is False


@pytest.mark.parametrize("message", [
    "elektrik faturamı nasıl öderim",
    "doğalgaz kesintisi ne zaman bitecek",
])
def test_out_of_scope_words_block_match(matcher, message):
    result = matcher.find_best_match(message)
    assert result["found"] is False
    assert result["out_of_scope"] is True


def test_out_of_scope_word_allowed_when_faq_contains_it(matcher):
    # "pasaport" kapsam dışı listesinde ama yabancı uyruklu evlilik SSS'sinde geçiyor
    result = matcher.find_best_match("yabancı uyruklu evlilik için pasaport gerekli mi")
    assert result["found"] is True
    assert result["out_of_scope"] is False
    assert result["faq"]["kategori"] == "Evlilik/Nikah İşlemleri"


def test_empty_matcher_does_not_crash():
    empty = FAQMatcher()
    empty.fit([])
    assert empty.find_best_match("su faturası")["found"] is False


def test_threshold_is_configurable(faqs):
    strict = FAQMatcher(threshold=0.99)
    strict.fit(faqs)
    assert strict.find_best_match("otobüs saatleri")["found"] is False


def test_suggestions_respect_limit_and_min_score(matcher):
    suggestions = matcher.suggestions("nikah", min_score=0.1, limit=3)
    assert 1 <= len(suggestions) <= 3
    assert all(s["kategori"] == "Evlilik/Nikah İşlemleri" for s in suggestions)


# ---------------------------------------------------------------------------
# Cevap üretimi (responses)
# ---------------------------------------------------------------------------

def test_greeting_response(matcher):
    result = build_response("Merhaba", matcher, 0.30, "Beyaz Masa")
    assert result["type"] == "greeting"
    assert result["offer_ticket"] is False


def test_not_found_response_offers_ticket_and_default_department(matcher):
    result = build_response("sokak lambası yanmıyor", matcher, 0.30, "Beyaz Masa")
    assert result["type"] == "not_found"
    assert result["offer_ticket"] is True
    assert result["department"] == "Beyaz Masa"
    assert "talep" in result["answer"].lower()


def test_out_of_scope_response(matcher):
    result = build_response("elektrik faturamı nasıl öderim", matcher, 0.30, "Beyaz Masa")
    assert result["type"] == "out_of_scope"
    assert result["offer_ticket"] is True
    assert result["department"] == "Beyaz Masa"
    assert result["suggestions"] == []


def test_found_response_contains_department(matcher):
    result = build_response("nikah salonu rezervasyonu", matcher, 0.30, "Beyaz Masa")
    assert result["type"] == "answer"
    assert result["department"] == "Evlendirme Memurluğu"
