"""
Chatbot doğruluk ölçümü.

Veritabanına veya Flask sunucusuna ihtiyaç duymadan, seed_data.json'daki demo SSS'lerle
chatbotun iki şeyi ne kadar iyi yaptığını ölçer:

  1) İLGİLİ sorular   : Farklı kelimelerle sorulan belediye soruları doğru kategoriye gidiyor mu?
  2) ALAKASIZ sorular : Belediyeyle ilgisi olmayan sorular reddediliyor mu ("cevap bulunamadı")?

Çalıştırmak için proje klasöründe:
    venv\\Scripts\\python.exe scripts\\dogruluk_olcumu.py
"""

import json
import os
import sys

# Proje kökünü import yoluna ekle
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from chatbot.matcher import FAQMatcher  # noqa: E402
from chatbot.responses import build_response  # noqa: E402
from config import Config  # noqa: E402

# (mesaj, beklenen kategori) — seed verisindeki sorularla birebir aynı OLMAYAN ifadeler
RELEVANT = [
    ("su faturası nasıl ödenir", "Su ve Kanalizasyon"),
    ("faturami nerden oderim", "Su ve Kanalizasyon"),
    ("suyumuz kesildi", "Su ve Kanalizasyon"),
    ("lağım taştı", "Su ve Kanalizasyon"),
    ("sayac bozuk", "Su ve Kanalizasyon"),
    ("imar durumu belgesi almak istiyorum", "İmar ve Şehircilik"),
    ("inşaat ruhsatı nasıl alınır", "İmar ve Şehircilik"),
    ("kaçak yapı ihbarı", "İmar ve Şehircilik"),
    ("iskan belgesi için ne gerekli", "İmar ve Şehircilik"),
    ("dükkan açmak için ruhsat", "Zabıta"),
    ("zabıtayı nasıl ararım", "Zabıta"),
    ("kaldırımı işgal eden dükkan", "Zabıta"),
    ("çöpler ne zaman toplanıyor", "Temizlik İşleri"),
    ("çöp kamyonu gelmedi", "Temizlik İşleri"),
    ("cop toplama gunleri", "Temizlik İşleri"),
    ("eski koltuğumu attırmak istiyorum", "Temizlik İşleri"),
    ("parktaki salıncak kırılmış", "Park ve Bahçeler"),
    ("ağaç budama talebi", "Park ve Bahçeler"),
    ("sokak köpekleri", "Park ve Bahçeler"),
    ("ücretsiz fidan dağıtımı", "Park ve Bahçeler"),
    ("evlenmek için gerekli belgeler", "Evlilik/Nikah İşlemleri"),
    ("nikah salonu rezervasyonu", "Evlilik/Nikah İşlemleri"),
    ("nikah şahidi kaç kişi olmalı", "Evlilik/Nikah İşlemleri"),
    ("nikah ücreti ne kadar", "Evlilik/Nikah İşlemleri"),
    ("emlak vergisi son ödeme tarihi", "Emlak/Vergi"),
    ("vergi borcumu sorgulamak istiyorum", "Emlak/Vergi"),
    ("borcumu taksitle ödeyebilir miyim", "Emlak/Vergi"),
    ("emekliler emlak vergisi öder mi", "Emlak/Vergi"),
    ("otobüs saatleri", "Ulaşım"),
    ("öğrenci kartı başvurusu", "Ulaşım"),
    ("otobüste çantamı unuttum", "Ulaşım"),
    ("trafik lambası bozuk", "Ulaşım"),
    ("kurslara kayıt", "Kültür ve Sosyal İşler"),
    ("sosyal yardım başvurusu", "Kültür ve Sosyal İşler"),
    ("kütüphane saatleri", "Kültür ve Sosyal İşler"),
    ("belediye etkinlik takvimi", "Kültür ve Sosyal İşler"),
    ("e-belediye şifremi unuttum", "Bilgi İşlem/BİMER"),
    ("wifi nerede var", "Bilgi İşlem/BİMER"),
    ("cimer başvurusu", "Bilgi İşlem/BİMER"),
    ("belediye sitesi açılmıyor", "Bilgi İşlem/BİMER"),
]

# Belediyenin SSS kapsamında olmayan sorular: hepsinin "cevap bulunamadı" olması beklenir
IRRELEVANT = [
    "hava durumu nasıl olacak",
    "bugün günlerden ne",
    "yarın hava yağışlı mı",
    "futbol maçı kaç kaç bitti",
    "pizza siparişi vermek istiyorum",
    "dolar kuru ne kadar",
    "en yakın eczane nerede",
    "hastane randevusu almak istiyorum",
    "ehliyet nasıl alınır",
    "elektrik faturamı nasıl öderim",
    "doğalgaz kesintisi ne zaman bitecek",
    "okul kayıtları ne zaman başlıyor",
    "askerlik yoklaması nereden yapılır",
    "bana bir fıkra anlat",
    "asdfgh qwerty",
]


# KONTROL SETİ: Stopword ve kapsam dışı listeleri ayarlanırken HİÇ kullanılmadı.
# Yöntemin daha önce görmediği sorulardaki gerçekçi başarısını gösterir.
# (mesaj, beklenen kategori) — beklenen None ise "reddedilmeli" demektir.
CONTROL = [
    ("su aboneliği iptal etmek istiyorum", "Su ve Kanalizasyon"),
    ("imar planına nasıl bakarım", "İmar ve Şehircilik"),
    ("iş yeri ruhsatı için hangi belgeler lazım", "Zabıta"),
    ("geri dönüşüm kutusu nerede", "Temizlik İşleri"),
    ("parktaki bank kırık", "Park ve Bahçeler"),
    ("yabancı biriyle evlenmek istiyorum", "Evlilik/Nikah İşlemleri"),
    ("tabela için reklam vergisi", "Emlak/Vergi"),
    ("65 yaş üstü ücretsiz kart", "Ulaşım"),
    ("ihtiyaç sahiplerine yardım başvurusu", "Kültür ve Sosyal İşler"),
    ("e-belediyeye nasıl kayıt olurum", "Bilgi İşlem/BİMER"),
    ("telefon faturamı ödemek istiyorum", None),
    ("kimlik kartımı yenilemek istiyorum", None),
    ("nöbetçi eczane hangisi", None),
    ("üniversite tercihleri ne zaman", None),
    ("namaz vakitleri", None),
    ("araba kiralamak istiyorum", None),
    ("kira artış oranı ne kadar", None),
    ("internet paketim bitti", None),
    ("vergi dairesi nerede", None),
    ("doğalgaz faturası çok yüksek geldi", None),
]


def load_faqs():
    with open(os.path.join(ROOT, "database", "seed_data.json"), encoding="utf-8") as f:
        data = json.load(f)
    return [
        {"kategori": c["kategori"], "departman": c["departman"], "soru": q["soru"],
         "cevap": q["cevap"], "anahtar_kelimeler": q.get("anahtar_kelimeler", "")}
        for c in data["kategoriler"] for q in c["sorular"]
    ]


def main():
    matcher = FAQMatcher(threshold=Config.SIMILARITY_THRESHOLD)
    matcher.fit(load_faqs())

    def ask(message):
        return build_response(message, matcher, Config.ROUTING_THRESHOLD, Config.DEFAULT_DEPARTMENT)

    print(f"Eşik: {Config.SIMILARITY_THRESHOLD}  |  Yönlendirme eşiği: {Config.ROUTING_THRESHOLD}\n")

    print("## İlgili sorular\n")
    print("| Mesaj | Beklenen | Skor | Sonuç |")
    print("|---|---|---|---|")
    relevant_ok = 0
    for message, expected in RELEVANT:
        r = ask(message)
        ok = r["found"] and r["category"] == expected
        relevant_ok += ok
        got = r["category"] or "bulunamadı"
        print(f"| {message} | {expected} | {r['score']:.2f} | {'✅' if ok else '❌ ' + got} |")

    print("\n## Alakasız sorular\n")
    print("| Mesaj | Skor | Sonuç |")
    print("|---|---|---|")
    irrelevant_ok = 0
    for message in IRRELEVANT:
        r = ask(message)
        ok = not r["found"]
        irrelevant_ok += ok
        detail = "✅ reddedildi" if ok else f"❌ yanlış eşleşme: {r['matched_question']}"
        print(f"| {message} | {r['score']:.2f} | {detail} |")

    print("\n## Kontrol seti (ayarlamada kullanılmadı)\n")
    print("| Mesaj | Beklenen | Skor | Sonuç |")
    print("|---|---|---|---|")
    control_ok = 0
    for message, expected in CONTROL:
        r = ask(message)
        if expected is None:
            ok = not r["found"]
            detail = "✅ reddedildi" if ok else f"❌ yanlış eşleşme: {r['matched_question']}"
        else:
            ok = r["found"] and r["category"] == expected
            detail = "✅" if ok else "❌ " + (r["category"] or "bulunamadı")
        control_ok += ok
        print(f"| {message} | {expected or 'reddedilmeli'} | {r['score']:.2f} | {detail} |")

    total = len(RELEVANT) + len(IRRELEVANT)
    print("\n## Özet\n")
    print(f"- Kontrol seti: **{control_ok}/{len(CONTROL)}** (%{100 * control_ok / len(CONTROL):.0f})")
    print(f"- İlgili sorularda doğru kategori: **{relevant_ok}/{len(RELEVANT)}** "
          f"(%{100 * relevant_ok / len(RELEVANT):.0f})")
    print(f"- Alakasız soruları reddetme: **{irrelevant_ok}/{len(IRRELEVANT)}** "
          f"(%{100 * irrelevant_ok / len(IRRELEVANT):.0f})")
    print(f"- Genel: **{relevant_ok + irrelevant_ok}/{total}** "
          f"(%{100 * (relevant_ok + irrelevant_ok) / total:.0f})")


if __name__ == "__main__":
    main()
