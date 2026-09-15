# Proje Analizi – Bulgular, Düzeltmeler ve Açık Kalanlar

> Bu proje bir staj çalışmasıdır. İçerdiği tüm veriler kurgusal demo verisidir, kurumun resmi verisi değildir.

**Analiz tarihi:** 15.09.2026
**Kapsam:** Tüm kaynak kodu (Python, JavaScript, HTML/CSS şablonları, `.bat` dosyaları), testler ve dokümanlar dosya dosya okundu. İddialar, çalışan uygulama üzerinde gerçek isteklerle ve tarayıcıda doğrulandı.

## Özet

| Grup | Bulgu sayısı | Durum |
|---|---|---|
| **1 – Teslimden önce mutlaka düzeltilmeli** | 7 | ✅ 7'si de düzeltildi |
| **2 – Düzeltilirse iyi olur** | 19 | ✅ 19'u da düzeltildi (riski düşük, hızlı olanlar) |
| **3 – Staj kapsamını aşar / ileride yapılabilir** | 13 | ⏳ Açık, sadece raporlandı |
| **Toplam** | **39** | 26 düzeltildi, 13 açık |

- Düzeltmelerden sonra test sayısı **56 → 108** oldu; hepsi geçiyor.
- Büyük mimari değişiklik gerektiren bir düzeltme yapılmadı.

**Efor ölçeği:** XS < 15 dk · S < 1 saat · M yarım gün · L 1–3 gün · XL 3 günden fazla

---

## Nasıl analiz edildi?

| Yöntem | Ne yapıldı? |
|---|---|
| Kod okuma | `app.py`, `config.py`, `database/db.py`, `chatbot/*.py`, `routes/*.py`, `static/js/*.js`, tüm şablonlar, `.bat` dosyaları, testler ve dokümanlar |
| Canlı API denemeleri | Liste/metin JSON gövdesi, 5 MB istek, emoji, sadece noktalama, İngilizce soru, 501 karakter, geçersiz telefon, liste türünde ad soyad |
| Tarayıcı denemeleri | Sohbete `<script>`, `<img onerror>`, `<svg onload>` gönderildi. Talep formuna aynı metinler yazıldı. Uzun soru ile talep oluşturuldu. Sunucu hatası taklit edildi. |
| Saldırı senaryosu | Kodda yazan varsayılan `SECRET_KEY` ile sahte admin oturum çerezi üretilip panele girmeye çalışıldı |
| Hata senaryoları | Bozuk/eksik `seed_data.json`, bozuk veritabanı dosyası, `.env`'de admin kullanıcı adının değiştirilmesi |
| Tarama | Tüm `execute(` çağrıları (SQL parametreli mi?), `innerHTML` / `eval` / `\|safe` kullanımı |
| Doküman kontrolü | README, rapor, sunum, savunma, test ve doğruluk belgelerindeki sayılar kodla karşılaştırıldı |

---

## Grup 1 – Teslimden önce mutlaka düzeltilmeli (✅ hepsi düzeltildi)

### 1.1 🔴 KRİTİK: Şifresiz admin girişi (herkese açık SECRET_KEY)

| | |
|---|---|
| **Etkilediği yer** | `config.py`, tüm admin paneli |
| **Sorun** | `.env` yoksa `SECRET_KEY = "gelistirme-icin-gizli-anahtar-degistirin"` kullanılıyordu. Bu değer GitHub'daki kodda herkese açık. Flask, admin girişini tarayıcı çerezine yazıp bu anahtarla imzalar. |
| **Doğrulama** | Bu anahtarla `{"admin_id": 1}` içeren sahte bir çerez imzalandı. `/admin/istatistik` sayfası **şifre girilmeden 200 döndü** ve panel açıldı. |
| **Neden önemli** | Uygulamaya ağdan erişebilen herkes talepleri, vatandaş adlarını ve telefonlarını görebilir; SSS'leri değiştirebilir veya silebilir. |
| **Çözüm** | `.env`'de gerçek bir anahtar yoksa rastgele 64 karakterlik anahtar üretilip `instance/secret_key` dosyasına kaydediliyor (bu dosya `.gitignore`'da). Herkese açık örnek değerler yok sayılıyor. |
| **Test** | `test_session_cookie_signed_with_old_public_key_is_rejected`, `test_public_placeholder_secret_key_is_ignored` |
| **Efor** | S |

### 1.2 🔴 Debug modu varsayılan olarak açık – hata ayrıntıları sızıyordu

| | |
|---|---|
| **Etkilediği yer** | `config.py` (`FLASK_DEBUG` varsayılanı `True`), `.env.example` |
| **Sorun** | Debug modunda beklenmeyen bir hata, Werkzeug hata ayıklayıcı sayfasını döndürür. |
| **Doğrulama** | `/api/chat` adresine `[1,2]` gönderildi. 14 KB'lık HTML cevapta `Traceback`, `api_routes.py` dosya yolu ve kaynak kod satırları görüldü. |
| **Neden önemli** | Sunucudaki klasör yapısı ve kod dışarıya sızar. Hata ayıklayıcı konsolu PIN ile korunsa da açık bir saldırı yüzeyidir. |
| **Çözüm** | `FLASK_DEBUG` varsayılanı `False` yapıldı. Beklenmeyen hatalar API'de `{"error": "..."}` olarak dönüyor; ayrıntı sadece sunucu konsoluna yazılıyor. |
| **Test** | `test_debug_mode_is_off_by_default`, `test_unexpected_error_returns_json_without_traceback` |
| **Efor** | XS |

### 1.3 🔴 Admin kullanıcı adı değişince eski hesap açık kalıyordu

| | |
|---|---|
| **Etkilediği yer** | `database/db.py` → `sync_admin_user` |
| **Sorun** | `.env`'de `ADMIN_USERNAME=yonetici` yapılınca yeni hesap ekleniyordu ama eski `admin / admin123` hesabı **silinmiyordu**. |
| **Doğrulama** | İki açılıştan sonra `admin` tablosu: `[('admin',), ('yonetici',)]` |
| **Neden önemli** | Kullanıcı şifresini güvenli hâle getirdiğini düşünürken herkesin bildiği demo hesabı çalışmaya devam eder. |
| **Çözüm** | Senkronizasyonda yapılandırılan kullanıcı dışındaki admin kayıtları siliniyor. Silinen hesabın açık oturumu da geçersiz sayılıyor. |
| **Test** | `test_changing_admin_username_removes_old_account`, `test_session_of_deleted_admin_is_invalidated` |
| **Efor** | XS |

### 1.4 🟠 JSON gövdesi nesne değilse 500 hatası

| | |
|---|---|
| **Etkilediği yer** | `routes/api_routes.py` → `/api/chat`, `/api/talep` |
| **Sorun** | `request.get_json(silent=True) or {}` ifadesi liste veya metin gövdesini olduğu gibi döndürüyor, ardından gelen `.get()` çağrısı çöküyordu. |
| **Doğrulama** | `[1,2]` ve `"abc"` gövdeleri → **HTTP 500** |
| **Çözüm** | `read_json_object()` yardımcısı nesne olmayan gövdeleri boş sözlük sayıyor; sonuç 400 ve Türkçe mesaj. |
| **Test** | `test_non_object_json_body_returns_400_not_500` (8 kombinasyon) |
| **Efor** | XS |

### 1.5 🟠 `.env.example` kopyalanınca yine herkese açık anahtar

| | |
|---|---|
| **Etkilediği yer** | `.env.example`, README kurulum adımı |
| **Sorun** | README `copy .env.example .env` öneriyordu. Dosyadaki `SECRET_KEY=buraya-uzun-ve-rastgele-bir-deger-yazin` değeri de herkese açık, yani 1.1 ile aynı açık oluşuyordu. |
| **Çözüm** | Örnek dosyada `SECRET_KEY=` boş bırakıldı ve nasıl üretileceği anlatıldı. Örnek değer yazılsa bile uygulama onu yok sayıyor. |
| **Efor** | XS |

### 1.6 🟠 Uzun soruyla talep oluşturulamıyordu

| | |
|---|---|
| **Etkilediği yer** | `static/js/chat.js` → `showTicketForm` |
| **Sorun** | “Evet, talep oluştur” denince vatandaşın sorusu “Konu” alanına yazılıyor. JavaScript ile yazılan değer `maxlength=150` sınırını aşabiliyor. |
| **Doğrulama** | 202 karakterlik soru → konu alanı 202 karakter → “Gönder” → *“En fazla 150 karakter girilebilir.”* Vatandaş metni kendisi kısaltmak zorunda kalıyordu. |
| **Neden önemli** | Talep oluşturma, chatbotun cevap veremediği durumdaki **ana akış**. Uzun şikayet yazan vatandaş tam da bu akışı kullanır. |
| **Çözüm** | Konu 150 karakterde “…” ile kısaltılıyor, sorunun tamamı “Açıklama” alanına yazılıyor. |
| **Efor** | XS |

### 1.7 🟠 Sunucu hatasında talep formu sessiz kalıyordu

| | |
|---|---|
| **Etkilediği yer** | `static/js/chat.js` |
| **Sorun** | `/api/talep` 500 veya 413 döndüğünde cevapta `errors` alanı yok. Form hiçbir mesaj göstermiyor, “Gönder” butonu eski hâline dönüyordu. |
| **Doğrulama** | Tarayıcıda 500 cevabı taklit edildi; formda hiçbir geri bildirim görülmedi. |
| **Çözüm** | Alan hatası yoksa formun altında `role="alert"` ile genel hata mesajı gösteriliyor. |
| **Efor** | XS |

---

## Grup 2 – Düzeltilirse iyi olur (✅ hepsi düzeltildi)

| # | Bulgu | Etkilediği yer | Neden önemli | Yapılan çözüm | Efor |
|---|---|---|---|---|---|
| 2.1 | Admin girişinde deneme sınırı yok | `admin_routes.py` | Şifre sınırsız denenerek tahmin edilebilir (kaba kuvvet) | IP başına 5 hatalı denemeden sonra 5 dakika kilit (HTTP 429) | S |
| 2.2 | Güvenlik başlıkları yok | `app.py` | Admin paneli başka bir sitenin iframe'inde açılabilir (clickjacking) | `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin` | XS |
| 2.3 | Oturum çerezinde SameSite yok, oturum süresiz | `config.py` | Tarayıcı kapanmadıkça admin oturumu açık kalır | `SameSite=Lax`, 8 saatlik oturum süresi | XS |
| 2.4 | İstek boyutu sınırı yok | `config.py` | 5 MB'lık istek belleğe tamamen okunduktan sonra reddediliyordu | `MAX_CONTENT_LENGTH = 64 KB`, 413 cevabı JSON | XS |
| 2.5 | Telefon doğrulaması zayıf | `api_routes.py` | `-------` veya `(((((((` geçerli telefon sayılıyordu | İzinli karakterler + 10–13 rakam kuralı | XS |
| 2.6 | Talep alanlarında tür kontrolü yok | `api_routes.py` | `"ad_soyad": ["x"]` gönderilince veritabanına `['x']` yazılıyordu | Metin olmayan değerlere “Geçersiz değer.” hatası | XS |
| 2.7 | Silinen admin hesabının oturumu geçerli kalıyor | `admin_routes.py` | Hesap silinse bile açık tarayıcı panele erişmeye devam eder | Her admin isteğinde hesabın veritabanında varlığı kontrol ediliyor | XS |
| 2.8 | Varsayılan şifre için uyarı yok | `app.py`, `base.html` | `admin123` herkese açık README'de yazıyor | Konsolda ve admin panelinin üstünde uyarı. Şifrenin kendisi demo için değiştirilmedi (bkz. “Senin yapman gerekenler”). | XS |
| 2.9 | SSS formunda sunucu tarafı uzunluk sınırı yok | `admin_routes.py` | HTML `maxlength` tarayıcıda atlatılabilir | Alan başına sınır (soru 300, cevap 3000…) | XS |
| 2.10 | Açılış hataları anlaşılmaz | `db.py`, `app.py`, `config.py` | Bozuk seed/veritabanında `basla.bat` penceresinde uzun bir Python hata çıktısı görünüyordu | Dosya adı ve çözüm öneren Türkçe mesaj (örn. *“sifirla.bat ile yeniden oluşturabilirsiniz”*). `.env`'deki hatalı sayı için de açık mesaj. | S |
| 2.11 | API hataları HTML dönüyor | `app.py` | Bilinmeyen `/api/…` adresi ve 405/413 cevapları HTML'di; sohbet penceresi anlamlı mesaj gösteremiyordu | `/api/` altındaki tüm HTTP hataları Türkçe JSON | XS |
| 2.12 | Model güncellemesi tek adımda değil | `chatbot/matcher.py` | Flask sunucusu çok iş parçacıklıdır. Admin SSS kaydederken aynı anda gelen mesaj yeni matris ile eski SSS listesini birlikte görüp hatalı eşleşebilir veya çökebilirdi. | Model parçaları tek bir `TrainedModel` nesnesinde; yeni model hazırlanıp tek atamayla devreye alınıyor | S |
| 2.13 | Cevap sözlüğü 4 kez tekrar ediliyor | `chatbot/responses.py` | Yeni alan eklemek 4 yeri değiştirmeyi gerektiriyordu | `make_reply()` yardımcı fonksiyonu | XS |
| 2.14 | Paket sürümleri üstten sınırsız | `requirements.txt` | İleride çıkacak scikit-learn 2.x gibi bir sürüm, yeni kurulumu bozabilir | `<2.0` gibi üst sınırlar | XS |
| 2.15 | Erişilebilirlik eksikleri (sohbet) | `chat.js`, `style.css` | Ekran okuyucu form hatalarını alanla ilişkilendiremiyor, “yazıyor” göstergesini seslendirmiyordu. Animasyonlar hareket hassasiyeti ayarını dikkate almıyordu. | `aria-invalid`, `aria-describedby`, `role="status"`, `prefers-reduced-motion` | S |
| 2.16 | Talep durumu seçilir seçilmez kaydediliyor | `talepler.html` | Klavyeyle ok tuşlarıyla gezinirken yanlış durum kaydedilebilir (WCAG 3.2.2) | Açık “Kaydet” butonu | XS |
| 2.17 | Selamlama cevabı var olmayan butonlardan bahsediyor | `responses.py`, `chat.js` | *“aşağıdaki hızlı sorulardan seçin”* deniyor ama buton gösterilmiyordu | Selamlamadan sonra konu butonları gösteriliyor | XS |
| 2.18 | Dokümanlarda hatalı/eski bilgi | `docs/` | Savunma belgesi *“veritabanı erişimi tek dosyada (db.py)”* diyordu (sorgular rota dosyalarında da var). Kılavuz durumun otomatik kaydedildiğini, README debug modunun varsayılan olarak açık olduğunu yazıyordu. | İlgili belgeler koddaki gerçek duruma göre güncellendi | S |
| 2.19 | Kritik yollar test edilmiyordu | `tests/` | Bozuk istekler, güvenlik ayarları, açılış hataları ve uç durumlar için test yoktu; 1.1–1.4 bu yüzden fark edilmemişti | `tests/test_guvenlik_ve_hatalar.py`: **52 yeni test** | M |

---

## Grup 3 – Staj kapsamını aşar / ileride yapılabilir (⏳ açık)

| # | Bulgu | Neden önemli | Önerilen çözüm | Efor |
|---|---|---|---|---|
| 3.1 | **Anlamı değil kelimeleri karşılaştırıyor** | Kontrol setinde alakasız 10 sorunun 5'i hâlâ yanlış eşleşiyor (*“telefon faturası” → su faturası*) | Yerel çalışan bir kelime vektörü/cümle gömme modeli ile anlamsal benzerlik; TF-IDF ile birlikte kullanılabilir | XL |
| 3.2 | Çıkış yapınca oturum sunucuda geçersizleşmiyor | Flask çerez tabanlı oturum kullanır; kopyalanan bir çerez 8 saat dolana kadar geçerlidir | Sunucu tarafı oturum deposu (Flask-Session) veya oturum sürümü tutma | M |
| 3.3 | İçerik Güvenlik Politikası (CSP) yok | XSS'e karşı ikinci savunma hattı olurdu | Önce satır içi `onsubmit` ve `<script>` blokları ayrı JS dosyalarına taşınmalı, sonra CSP başlığı eklenmeli | M |
| 3.4 | Genel API'de hız sınırı yok | `/api/talep` ile otomatik sahte talep gönderilebilir; `chat_log` sınırsız büyür | Yayında ters vekil sunucu (nginx) seviyesinde hız sınırı veya Flask-Limiter; talep formuna basit doğrulama | M |
| 3.5 | KVKK: veri saklama ve aydınlatma | Sohbet mesajları ve talepteki ad/telefon süresiz saklanıyor; formda aydınlatma metni/onay yok | Kurum hukuk birimiyle saklama süresi belirlenmeli; eski kayıtları silen görev ve formda aydınlatma metni bağlantısı | M |
| 3.6 | Geliştirme sunucusu, HTTPS yok, tek süreç | `app.run()` üretim için uygun değil; birden çok süreçte admin'in SSS güncellemesi diğer süreçlerin modelini yenilemez | Waitress + IIS/nginx + HTTPS; çok süreçte model yenilemesi için veritabanında “SSS sürümü” kontrolü | L |
| 3.7 | Sohbet geçmişinde sayfalama yok | Sadece son 200 kayıt görülebiliyor | `LIMIT/OFFSET` ile sayfalama ve tarih filtresi | S |
| 3.8 | Selamlamalar “cevaplanan” sayılıyor | *“merhaba”* mesajları cevaplanma oranını olduğundan yüksek gösterir | `chat_log` tablosuna cevap türü sütunu eklenip istatistikte hariç tutulması (şema değişikliği gerektirir) | S |
| 3.9 | JavaScript için otomatik test yok | Sohbet widget'ı sadece elle ve tarayıcıda test edildi | Playwright ile uçtan uca tarayıcı testleri | M |
| 3.10 | JavaScript kapalıyken sohbet ve hızlı sorular çalışmıyor; site dışı hata sayfaları İngilizce | Az sayıda kullanıcıyı etkiler | `<noscript>` uyarısı ve Türkçe 404/500 şablonları | S |
| 3.11 | Klavyeyle sohbet balonuna ulaşmak uzun sürüyor | Balon sayfanın en sonunda; klavye kullanıcısı tüm hızlı soruları geçmek zorunda (“Asistanla Konuş” butonu alternatif sunuyor) | Sayfa başına “Sohbete geç” atlama bağlantısı | XS |
| 3.12 | Tek admin hesabı, rol yok | Her birim sadece kendi taleplerini görmeli | Kullanıcı tablosu, rol ve birim bazlı yetkilendirme | L |
| 3.13 | Eşik değerleri kurgusal veriyle ayarlandı | Gerçek vatandaş sorularında 0.35 en iyi değer olmayabilir | Gerçek SSS ve anonimleştirilmiş sohbet kayıtlarıyla `scripts/dogruluk_olcumu.py` yeniden çalıştırılmalı | S |

---

## İncelenen ve sorun bulunmayan konular

| Konu | Sonuç | Kanıt |
|---|---|---|
| Sohbette XSS | ✅ Güvenli. Mesajlar `textContent` ile yazılıyor; `innerHTML`, `eval` veya `\|safe` yok. | Tarayıcıda `<script>`, `<img onerror>`, `<svg onload>` denendi: kod çalışmadı, DOM'a eleman eklenmedi |
| Admin sayfalarında XSS | ✅ Jinja2 otomatik kaçışlama çalışıyor; grafik verisi `tojson` ile güvenli | `test_xss_payloads_are_escaped_in_admin_pages` |
| SQL injection | ✅ Tüm `execute` çağrıları `?` parametreli. Dinamik sorgular sadece sabit metin parçalarından oluşuyor. | Kod taraması + `test_chat_sql_injection_text_is_stored_safely` |
| CSRF | ✅ Tüm admin POST formlarında token var. JSON API'ler `application/json` gerektirdiği için başka sitelerden basit form ile çağrılamıyor. | `test_admin_post_without_csrf_is_rejected` |
| Şifre saklama | ✅ Werkzeug scrypt hash | `test_admin_password_is_hashed` |
| Açık yönlendirme | ✅ `next` parametresi sadece `/admin` ile başlayan adresleri kabul ediyor | Kod incelemesi |
| Veritabanı bağlantıları | ✅ İstek sonunda `teardown_appcontext` ile, açılışta `finally` ile kapatılıyor | Kod incelemesi |
| TF-IDF performansı | ✅ Model her istekte değil, açılışta ve SSS değişince eğitiliyor. Cevap bulunamadığında öneriler için benzerlik ikinci kez hesaplanıyor; 70 SSS'de ihmal edilebilir. | Kod incelemesi |
| Boş, çok uzun, emoji, sadece noktalama, İngilizce mesaj | ✅ 400 veya düzgün “bulunamadı” cevabı; çökme yok | Canlı istekler + `test_edge_case_messages_do_not_crash` |
| Enter ile gönderme, Esc ile kapatma | ✅ Form `submit` olayı ve `keydown` dinleyicisi | Kod incelemesi + tarayıcı |
| Mobil görünüm | ✅ 390 px'te yatay taşma yok, sohbet tam ekran | Önceki tarayıcı ölçümleri |
| Dokümanlardaki sayılar | ✅ 70 SSS, 10 kategori, doğruluk oranları kodla uyuşuyor. Test sayısı 108 olarak güncellendi. | Tarama + `pytest --collect-only` |

---

## Senin yapman gerekenler

1. **Gerçek bir sunucuda çalıştırılacaksa** `.env` dosyası oluşturup `ADMIN_PASSWORD` değerini değiştir. Demo için `admin123` bilerek bırakıldı; panelde bununla ilgili uyarı çıkıyor.
2. **Eski admin oturumları:** Gizli anahtar değiştiği için güncellemeden önce açılmış admin oturumları kapandı; bir kez yeniden giriş yapman gerekecek.
3. Sunumda güvenlik sorulursa bu belgedeki **1.1** bulgusu iyi bir örnek: *“Analiz sırasında kritik bir açık buldum, testle kanıtladım ve düzelttim.”*
