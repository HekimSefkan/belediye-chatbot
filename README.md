> **Bu proje bir staj çalışmasıdır. İçerdiği tüm veriler kurgusal demo verisidir, kurumun resmi verisi değildir.**

# Mardin Büyükşehir Belediyesi – Vatandaş Hizmetleri Chatbotu

Mardin Büyükşehir Belediyesi Bilgi İşlem Dairesi Başkanlığı'ndaki zorunlu yaz stajı kapsamında geliştirilmiş, **tamamen yerelde (offline) çalışan** bir web chatbotu.

Vatandaşın yazdığı soruyu belediyenin sık sorulan sorularıyla (SSS) karşılaştırır:

- Benzerlik skoru **0.35 ve üzerindeyse** en uygun cevabı ve sorumlu birimi gösterir.
- Skor eşiğin altındaysa vatandaşı **ilgili birime yönlendirir**, benzer soruları önerir ve **“Talep olarak kaydedeyim mi?”** diye sorar.
- Admin panelinden SSS'ler yönetilir, talepler takip edilir ve kullanım istatistikleri grafiklerle izlenir.

Ücretli hiçbir API veya harici servis kullanılmaz; eşleştirme **TF-IDF + cosine similarity** (scikit-learn) ile yapılır.

---

## İçindekiler

- [Özellikler](#özellikler)
- [Kullanılan teknolojiler](#kullanılan-teknolojiler)
- [Kurulum](#kurulum-windows)
- [Testleri çalıştırma](#testleri-çalıştırma)
- [Kullanım senaryosu](#kısa-kullanım-senaryosu)
- [Proje yapısı](#proje-yapısı)
- [Chatbot nasıl çalışır?](#chatbot-nasıl-çalışır)
- [Güvenlik önlemleri](#güvenlik-önlemleri)
- [Sınırlılıklar ve geliştirme fikirleri](#sınırlılıklar-ve-geliştirme-fikirleri)
- [Dokümanlar](#dokümanlar)

---

## Özellikler

**Vatandaş tarafı**
- Sağ altta açılan sohbet balonu (mobil uyumlu, telefonda tam ekran)
- Kategori bazlı **Hızlı Sorular**, hem sayfada hem sohbet penceresinde
- Türkçe karakter kullanmadan yazılan soruları da anlama (`cop toplama gunleri` → Temizlik İşleri)
- Cevap bulunamadığında birim yönlendirmesi, benzer soru önerileri ve sohbet içinde **talep/şikayet formu**
- Talep oluşturulunca vatandaşa talep numarası verilmesi

**Admin paneli** (`/admin`)
- Oturum tabanlı giriş (şifre hash'lenmiş olarak saklanır)
- **İstatistikler:** toplam soru, cevaplanamayan soru oranı, en çok sorulan kategoriler, son 7 gün grafikleri (Chart.js)
- **SSS Yönetimi:** ekle / düzenle / sil, kategori filtresi ve arama. Değişiklikler chatbota **anında** yansır.
- **Talep / Şikayetler:** listeleme, duruma göre filtreleme, durum güncelleme (Beklemede → İşlemde → Tamamlandı)
- **Sohbet Geçmişi:** tüm mesajlar. Cevaplanamayan bir soru tek tıkla SSS'ye eklenebilir.

## Kullanılan teknolojiler

| Katman | Teknoloji | Neden? |
|---|---|---|
| Backend | Python 3.11+, Flask | Öğrenmesi kolay, hafif ve yaygın web çatısı |
| Veritabanı | SQLite | Kurulum gerektirmez, tek dosya |
| Doğal dil eşleştirme | scikit-learn (TF-IDF + cosine similarity) | Ücretsiz, offline, sonuçları açıklanabilir |
| Frontend | HTML, düz CSS, vanilla JavaScript | Ek kütüphane yok, kolay anlaşılır |
| Grafikler | Chart.js 4 (projede yerel dosya) | Kurumsal ağda internet olmasa da çalışır |
| Test | pytest | Python'un standart test aracı |
| Güvenlik | Werkzeug (şifre hash'leme) | Flask ile birlikte gelir |

---

## Kurulum (Windows)

> Gereksinim: **Python 3.11 veya üzeri**. Kurulu olup olmadığını `python --version` komutuyla kontrol edebilirsiniz.

PowerShell'i proje klasöründe açın ve sırasıyla şu komutları çalıştırın:

```powershell
# 1) Sanal ortam oluştur
python -m venv venv

# 2) Sanal ortamı etkinleştir
venv\Scripts\activate

# 3) Gerekli paketleri yükle
pip install -r requirements.txt

# 4) (İsteğe bağlı) Ayar dosyasını oluştur ve admin şifresini değiştir
copy .env.example .env

# 5) Uygulamayı başlat
python app.py
```

Tarayıcıda açın:

- Chatbot: **http://127.0.0.1:5000**
- Admin paneli: **http://127.0.0.1:5000/admin**
  (varsayılan kullanıcı adı `admin`, şifre `admin123`. `.env` dosyasından değiştirilebilir.)

İlk çalıştırmada `database/chatbot.db` dosyası otomatik oluşturulur ve 70 demo SSS kaydı yüklenir. Veritabanını sıfırlamak için uygulamayı durdurup bu dosyayı silmeniz yeterlidir.

> **PowerShell “betik çalıştırma devre dışı” hatası verirse:** Önce `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` komutunu çalıştırın. Ya da sanal ortamı etkinleştirmeden `venv\Scripts\python.exe app.py` ile başlatın.

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

### Ayarlar (`.env`)

| Değişken | Varsayılan | Açıklama |
|---|---|---|
| `SECRET_KEY` | geliştirme anahtarı | Oturum çerezlerini imzalar. Gerçek ortamda mutlaka değiştirin. |
| `ADMIN_USERNAME` | `admin` | Admin kullanıcı adı |
| `ADMIN_PASSWORD` | `admin123` | Admin şifresi. Uygulama her açıldığında hash'lenip veritabanına yazılır. |
| `SIMILARITY_THRESHOLD` | `0.35` | Cevabın “bulundu” sayılması için gereken en düşük benzerlik skoru |
| `FLASK_DEBUG` | `True` | Geliştirme modu |
| `PORT` | `5000` | Sunucu portu |

## Testleri çalıştırma

```powershell
pytest -v
```

48 test bulunur: metin ön işleme, TF-IDF eşleştirme doğruluğu, `/api/chat` ve `/api/talep` uç noktaları, admin girişi, CSRF koruması, SSS CRUD, talep durum güncelleme ve SQL injection denemesi. Testler geçici bir veritabanı kullanır; gerçek `chatbot.db` dosyasına dokunmaz.

---

## Kısa kullanım senaryosu

1. **Vatandaş cevabı hazır bir soru soruyor.** Ana sayfada sağ alttaki balona tıklar ve *“çöpler hangi gün toplanıyor”* yazar. Asistan Temizlik İşleri'ne ait cevabı gösterir, altında *“Temizlik İşleri · İlgili birim: Temizlik İşleri Dairesi Başkanlığı”* bilgisi yer alır.
2. **Türkçe karakter olmadan yazıyor.** *“faturami nerden oderim”* yazar. Ön işleme sayesinde soru yine su faturası cevabıyla eşleşir.
3. **Hızlı soru seçiyor.** Sayfadaki “Hızlı Sorular” bölümünden *“Nikah başvurusu için hangi belgeler gerekiyor?”* sorusuna tıklar. Sohbet açılır ve cevap gelir.
4. **Cevabı olmayan bir soru soruyor.** *“sokak lambası yanmıyor”* yazar. Asistan net bir cevap bulamadığını söyler, vatandaşı Beyaz Masa'ya yönlendirir ve *“Talep olarak kaydetmemi ister misiniz?”* diye sorar.
5. **Talep oluşturuyor.** *“Evet, talep oluştur”* butonuna basar. Konu ve birim önceden doldurulmuş form açılır. Ad soyad ve açıklamayı yazıp gönderir, *“Talebiniz #1 numarasıyla … iletildi”* mesajını görür.
6. **Admin talebi işliyor.** `/admin` adresinden giriş yapar. **Talep / Şikayetler** sayfasında #1 numaralı talebin durumunu *İşlemde* yapar.
7. **Admin chatbotu geliştiriyor.** **İstatistikler** sayfasında cevaplanamayan oranını ve kategori grafiğini inceler. “Son cevaplanamayan sorular” tablosunda *“sokak lambası yanmıyor”* satırındaki **SSS olarak ekle** bağlantısına tıklar, cevabı yazıp kaydeder. Aynı soru chatbota tekrar sorulduğunda artık cevap gelir.

Daha ayrıntılı demo adımları için: [docs/test_senaryolari.md](docs/test_senaryolari.md)

---

## Proje yapısı

```
mardin-belediye-chatbot/
├── app.py                  # Flask giriş noktası (application factory)
├── config.py               # Ayarlar (.env'den okunur)
├── requirements.txt
├── .env.example            # Örnek ayar dosyası
├── database/
│   ├── schema.sql          # Tablo tanımları
│   ├── seed_data.json      # 10 kategori, 70 kurgusal demo SSS
│   └── db.py               # Bağlantı, kurulum ve ortak sorgular
├── chatbot/
│   ├── preprocessor.py     # Türkçe metin temizleme (küçük harf, karakter, stopword, kök)
│   ├── matcher.py          # TF-IDF + cosine similarity eşleştirme
│   └── responses.py        # Eşleşme sonucunu vatandaş cevabına dönüştürme
├── routes/
│   ├── chat_routes.py      # Ana sayfa
│   ├── api_routes.py       # /api/chat, /api/talep, /api/hizli-sorular, /api/departmanlar
│   └── admin_routes.py     # Admin paneli (giriş, istatistik, SSS, talepler, sohbet geçmişi)
├── templates/              # Jinja2 HTML şablonları (index.html + admin/)
├── static/
│   ├── css/                # style.css (vatandaş), admin.css (panel)
│   └── js/                 # chat.js, admin_charts.js, chart.umd.min.js (yerel Chart.js)
├── tests/                  # pytest testleri
└── docs/                   # Mimari, veritabanı, kullanıcı kılavuzu, test senaryoları
```

## Chatbot nasıl çalışır?

```
"Su faturamı nasıl ödeyebilirim?"
        │ 1) Ön işleme: küçük harf → Türkçe karakter → noktalama → stopword → ilk 5 harf
        ▼
"su fatur odeye"
        │ 2) TF-IDF vektörüne dönüştürme
        ▼
[0.00, 0.61, 0.00, 0.43, ...]
        │ 3) 70 SSS vektörüyle cosine similarity
        ▼
En yüksek skor: 0.66  →  "Su faturamı nasıl ödeyebilirim?"
        │ 4) Skor ≥ 0.35 ise cevap, değilse yönlendirme + talep teklifi
        ▼
Cevap + "Su ve Kanalizasyon Dairesi Başkanlığı"
```

- **TF-IDF:** Bir kelime bir soruda sık, diğer sorularda seyrek geçiyorsa o kelimenin ağırlığı yüksek olur. Örneğin *“iskan”* ayırt edici bir kelimedir, *“belediye”* değildir.
- **Cosine similarity:** İki vektör arasındaki açının kosinüsüdür. 1 değeri tamamen aynı kelimeler, 0 değeri hiç ortak kelime olmadığı anlamına gelir.
- **Kök bulma (F5):** Türkçe eklemeli bir dildir. *“faturamı / faturası / faturayı”* kelimelerinin ilk 5 harfi alınarak hepsi *“fatur”* köküne indirgenir. Harici kütüphane gerektirmeyen basit bir yöntemdir.
- Model uygulama açılırken bir kez eğitilir ve bellekte tutulur. SSS eklenince, düzenlenince veya silinince yeniden eğitilir.

Ayrıntılı diyagramlar: [docs/mimari_diyagram.md](docs/mimari_diyagram.md)

## Güvenlik önlemleri

- **SQL injection:** Tüm sorgular `?` yer tutucularıyla (parametreli) yazılmıştır. Bunu doğrulayan bir test de vardır.
- **Şifre saklama:** Admin şifresi `werkzeug.security` ile hash'lenir, veritabanında düz metin tutulmaz.
- **CSRF:** Admin panelindeki tüm POST formları oturuma özel bir token ile korunur.
- **XSS:** Sohbet mesajları ekrana `textContent` ile yazılır. Jinja2 şablonları çıktıları otomatik olarak kaçışlar (escape).
- **Girdi doğrulama:** Mesaj ve form alanlarında uzunluk sınırı, telefon formatı ve departman listesi kontrolleri yapılır.
- **Oturum:** Girişte oturum yenilenir (session fixation önlemi), yönlendirmeler yalnızca site içi adreslere yapılır.
- `.env` ve veritabanı dosyası `.gitignore` sayesinde GitHub'a yüklenmez.

## Sınırlılıklar ve geliştirme fikirleri

- TF-IDF **kelime** benzerliğine bakar, **anlama** bakmaz. Örneğin *“hava durumu”* sorusu, *“imar durum belgesi”* sorusuyla ortak kelime içerdiği için yanlış eşleşebilir. Eş anlamlı kelimeler SSS'nin *anahtar kelimeler* alanına eklenerek başarı artırılabilir.
- Yazım hatalarına toleransı sınırlıdır. İleride Levenshtein mesafesi ile iyileştirilebilir.
- Tek admin kullanıcısı vardır, rol yönetimi yoktur.
- Olası geliştirmeler: sesli soru (Web Speech API), Telegram botu, talep durumunu vatandaşın sorgulayabilmesi. İsteğe bağlı olarak bir LLM katmanı da eklenebilir, ancak bu *ücretli/harici servis gerektirdiği için kurumsal ortamda kullanılmayabilir.*

## Dokümanlar

- [Mimari diyagram](docs/mimari_diyagram.md)
- [Veritabanı şeması](docs/veritabani_semasi.md)
- [Kullanıcı kılavuzu](docs/kullanici_kilavuzu.md)
- [Test senaryoları ve sonuçları](docs/test_senaryolari.md)
