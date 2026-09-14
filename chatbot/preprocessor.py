"""
Metin ön işleme (preprocessing) modülü.

Vatandaşın yazdığı mesaj ile SSS'deki sorular karşılaştırılmadan önce
aynı "temiz" biçime getirilir. Adımlar:

  1. Türkçeye uygun küçük harfe çevirme  ("İMAR" -> "imar", "ISIK" -> "ışık")
  2. Türkçe karakter normalizasyonu     ("çöp" -> "cop")
     -> Klavyesinde Türkçe karakter olmayan kullanıcı "cop" yazsa da eşleşir.
  3. Noktalama ve özel karakter temizliği
  4. Stopword (anlamsız bağlaç/soru eki) çıkarma ("ve", "mi", "nasil" ...)
  5. Basit kök bulma: kelimenin ilk 5 harfini alma (F5 yöntemi)
     -> "faturamı", "faturası", "faturayı" hepsi "fatur" olur.
     Türkçe gibi eklemeli dillerde bilgi erişimi çalışmalarında kullanılan,
     ek kütüphane gerektirmeyen basit ve etkili bir yöntemdir.
"""

import re

# Kelimenin kaç harfinin "kök" olarak tutulacağı (F5 yöntemi)
STEM_LENGTH = 5

# Türkçe karakterleri İngilizce karşılıklarına çeviren tablo
TURKISH_CHAR_MAP = str.maketrans("çğıöşüâîû", "cgiosuaiu")

# Anlam taşımayan, çok sık geçen kelimeler.
# Not: Liste, normalizasyon SONRASI hâliyle yazılmıştır (ç->c, ı->i vb.).
STOPWORDS = {
    # bağlaçlar ve edatlar
    "ve", "veya", "ile", "ya", "da", "de", "ki", "ama", "fakat", "ancak",
    "icin", "gibi", "kadar", "hem", "yani", "ise", "diye",
    # zamirler
    "ben", "beni", "bana", "benim", "sen", "seni", "sana", "senin",
    "biz", "bize", "bizi", "bizim", "siz", "size", "sizi", "sizin",
    "o", "ona", "onu", "onun", "bu", "buna", "bunu", "bunun", "su", "suna", "sunu",
    # soru kelimeleri ve soru ekleri
    "mi", "mu", "misin", "misiniz", "miyim", "musunuz", "midir", "mudur",
    "ne", "neden", "niye", "nasil", "nerede", "nereden", "nereye", "hangi",
    "kim", "kime", "kac", "acaba",
    # nezaket ve dolgu kelimeleri
    "lutfen", "rica", "ederim", "bir", "biri", "bazi", "cok", "daha", "en",
    "her", "hic", "sey", "icinde", "var", "mevcut", "hakkinda",
    # her konuda geçebilen genel fiiller (tek başına konu belirtmez)
    "istiyorum", "istiyoruz", "isterim", "yapmak", "yapmaliyim", "yapabilirim",
    "olabilir", "olur", "nedir", "lazim", "vermek", "etmek",
    "olacak", "olacakmi", "olsun", "oluyor", "olmali", "bitecek",
    # genel zaman ve durum kelimeleri
    # ("hava durumu" sorusunun "imar durum belgesi" ile eşleşmesini engeller)
    "durum", "durumu", "durumunu", "durumum", "zaman", "simdi",
    "bugun", "yarin", "gun", "gunu", "gunler", "gunleri", "gunlerden",
}

# DİKKAT: "su" hem zamir (şu) hem de "su" (içme suyu) anlamına geliyor.
# Belediye chatbotunda "su" kelimesi çok önemli olduğu için stopword'den çıkarıyoruz.
STOPWORDS.discard("su")

# Belediyenin görev alanı DIŞINDA kalan konuları gösteren kelimeler.
# Bu kelimelerden biri mesajda geçiyor ama eşleşen SSS'nin metninde geçmiyorsa
# eşleşme reddedilir. Örnek: "elektrik faturamı nasıl öderim" sorusu,
# ortak "fatura" kelimesi yüzünden su faturası cevabıyla eşleşmemeli.
# Bir SSS bu kelimelerden birini gerçekten içeriyorsa (örn. anahtar kelimelerde
# "pasaport") o SSS için engel uygulanmaz.
OUT_OF_SCOPE_WORDS = {
    "elektrik", "dogalgaz", "hava", "havalar", "ehliyet", "pasaport",
    "hastane", "eczane", "okul", "universite", "askerlik",
    "futbol", "mac", "maci", "dolar", "euro", "doviz", "borsa",
}


def turkish_lower(text):
    """
    Türkçe kurallarına uygun küçük harfe çevirir.
    Python'un lower() fonksiyonu "I" harfini "i" yapar; Türkçede doğrusu "ı"dır.
    Bu yüzden önce I/İ harflerini elle dönüştürüyoruz.
    """
    return text.replace("I", "ı").replace("İ", "i").lower()


def normalize_text(text):
    """
    Adım 1-3: küçük harf + Türkçe karakter normalizasyonu + noktalama temizliği.
    Stopword çıkarmaz, kök bulmaz (selamlama tespiti gibi yerlerde kullanılır).
    """
    if not text:
        return ""
    text = turkish_lower(text)
    text = text.translate(TURKISH_CHAR_MAP)
    # Harf ve rakam dışındaki her şeyi boşluğa çevir (noktalama, emoji vb.)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    # Birden fazla boşluğu tek boşluğa indir
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text):
    """Normalleştirilmiş metni kelimelere (token) böler."""
    return normalize_text(text).split()


def stem(word):
    """Basit kök bulma: kelimenin ilk STEM_LENGTH harfi (rakamlar olduğu gibi kalır)."""
    if word.isdigit():
        return word
    return word[:STEM_LENGTH]


def clean_text(text):
    """
    Tüm ön işleme adımlarını uygular ve TF-IDF'e verilecek metni döndürür.

    Örnek:
        clean_text("Su faturamı nasıl ödeyebilirim?")  ->  "su fatur odeye"
    """
    tokens = [stem(t) for t in tokenize(text) if t not in STOPWORDS]
    return " ".join(tokens)


# Kapsam dışı kelimelerin kök hâlleri (clean_text çıktısıyla karşılaştırabilmek için)
OUT_OF_SCOPE_STEMS = {stem(word) for word in OUT_OF_SCOPE_WORDS}
