# Test Senaryoları ve Sonuçları

> Bu proje bir staj çalışmasıdır. İçerdiği tüm veriler kurgusal demo verisidir, kurumun resmi verisi değildir.

Bu belge dört bölümden oluşur:

1. **Otomatik testler (pytest):** Kod değiştiğinde tek tıkla tekrar çalıştırılabilir.
2. **Doğruluk ölçümü:** Chatbotun farklı ifade edilmiş sorulardaki başarısı.
3. **Uçtan uca manuel senaryolar:** Sunum/demo sırasında tarayıcıda uygulanacak adımlar.
4. **Kurulum ve çalıştırma testleri:** `.bat` dosyalarının doğrulanması.

---

## 1. Otomatik testler

Çalıştırma: **`testleri_calistir.bat`** dosyasına çift tıklayın ya da:

```powershell
.\venv\Scripts\python.exe -m pytest -v
```

**Son çalıştırma (15.09.2026, `C:\Projects\belediye-chatbot`):** `122 passed`

| Dosya | Test sayısı |
|---|---|
| `tests/test_matcher.py` | 34 |
| `tests/test_api.py` | 21 |
| `tests/test_admin_akisi.py` | 1 |
| `tests/test_guvenlik_ve_hatalar.py` | 52 |
| `tests/test_teslim_oncesi.py` | 14 |
| **Toplam** | **122** |

### `tests/test_matcher.py` – Ön işleme ve eşleştirme (34 test)

| Test | Neyi doğrular? |
|---|---|
| `test_turkish_lower_handles_dotted_and_dotless_i` | `İ → i`, `I → ı` dönüşümü doğru |
| `test_normalize_removes_turkish_chars_and_punctuation` | `ç ö ı` gibi karakterler ve noktalama temizleniyor |
| `test_clean_text_removes_stopwords_and_stems` | `"Su faturamı nasıl ödeyebilirim?" → "su fatur odeye"` |
| `test_clean_text_same_root_for_different_suffixes` | `faturamı / faturası / faturayı` aynı köke iniyor |
| `test_clean_text_empty_input` | Boş ve sadece noktalamadan oluşan girdi hata vermiyor |
| `test_seed_data_size` | Demo veri seti 8-10 kategori ve 60-80 soru içeriyor |
| `test_exact_question_matches_itself` | 70 SSS'nin her biri kendisiyle eşleşiyor |
| `test_paraphrased_questions_match_correct_category` (11 örnek) | Farklı ifade edilmiş sorular doğru kategoriye gidiyor |
| `test_unrelated_messages_are_below_threshold` (3 örnek) | Konu dışı mesajlar eşleşmiyor |
| `test_only_stopwords_returns_not_found` | Sadece bağlaçlardan oluşan mesaj eşleşmiyor |
| `test_generic_words_no_longer_cause_false_match` (2 örnek) | *“hava durumu”*, *“bugün günlerden ne”* artık yanlış eşleşmiyor |
| `test_out_of_scope_words_block_match` (2 örnek) | *“elektrik faturası”*, *“doğalgaz kesintisi”* kapsam dışı olarak reddediliyor |
| `test_out_of_scope_word_allowed_when_faq_contains_it` | *“pasaport”* kelimesini içeren SSS (yabancı evlilik) eşleşmeye devam ediyor |
| `test_empty_matcher_does_not_crash` | SSS tablosu boşken uygulama çökmüyor |
| `test_threshold_is_configurable` | Eşik değeri ayardan değiştirilebiliyor |
| `test_suggestions_respect_limit_and_min_score` | Öneri listesi en fazla 3 kayıt ve doğru kategori içeriyor |
| `test_greeting_response` | “Merhaba” mesajına selamlama cevabı veriliyor |
| `test_not_found_response_offers_ticket_and_default_department` | Cevap yoksa talep teklif ediliyor, Beyaz Masa'ya yönlendiriliyor |
| `test_out_of_scope_response` | Kapsam dışı cevap tipi, talep teklifi var, öneri yok |
| `test_found_response_contains_department` | Bulunan cevapta departman bilgisi var |

### `tests/test_api.py` – API ve admin paneli (21 test)

| Test | Neyi doğrular? |
|---|---|
| `test_chat_returns_answer_for_known_question` | `/api/chat` bilinen soruya 200 ve doğru kategoriyle cevap veriyor |
| `test_chat_is_logged_to_database` | Mesaj, skor ve kategori `chat_log` tablosuna yazılıyor |
| `test_chat_unknown_question_offers_ticket` | Bilinmeyen soruda `offer_ticket: true`, log'da `cevap_bulundu_mu = 0` |
| `test_chat_out_of_scope_question` | *“doğalgaz faturası çok yüksek geldi”* kapsam dışı olarak Beyaz Masa'ya yönlendiriliyor |
| `test_chat_greeting` | Selamlama tipi cevap dönüyor |
| `test_chat_rejects_empty_message` | Boş mesaj, eksik alan ve JSON olmayan istek 400 dönüyor |
| `test_chat_rejects_too_long_message` | 500 karakterden uzun mesaj reddediliyor |
| `test_chat_sql_injection_text_is_stored_safely` | `x'); DROP TABLE faq; --` tabloyu silmiyor, metin olarak saklanıyor |
| `test_create_ticket_success` | `/api/talep` 201 dönüyor, kayıt `Beklemede` durumunda oluşuyor |
| `test_create_ticket_validation_errors` | Eksik/hatalı alanların hepsi için hata mesajı dönüyor |
| `test_quick_questions_endpoint` | Hızlı sorular kategori bazında dönüyor |
| `test_departments_endpoint_includes_default` | Departman listesinde Beyaz Masa var |
| `test_index_page` | Ana sayfa açılıyor ve demo veri uyarısını içeriyor |
| `test_admin_pages_require_login` | Giriş yapılmadan admin sayfaları giriş ekranına yönlendiriyor |
| `test_admin_password_is_hashed` | Şifre veritabanında hash olarak saklanıyor |
| `test_admin_login_wrong_password` | Yanlış şifreyle oturum açılmıyor |
| `test_admin_post_without_csrf_is_rejected` | CSRF token'ı olmayan form 400 dönüyor |
| `test_admin_pages_render_after_login` | Tüm admin sayfaları giriş sonrası hatasız açılıyor |
| `test_admin_faq_create_updates_chatbot` | Admin'in eklediği SSS'yi chatbot hemen cevaplayabiliyor |
| `test_admin_faq_delete` | SSS silme çalışıyor |
| `test_admin_ticket_status_update` | Talep durumu güncelleniyor, geçersiz durum kabul edilmiyor |

### `tests/test_admin_akisi.py` – Admin panelinin uçtan uca kullanımı (1 senaryo testi)

`test_admin_full_walkthrough`, bir yöneticinin paneldeki tüm işlerini **gerçek HTTP istekleriyle sırasıyla** dener:

| Adım | Doğrulanan davranış |
|---|---|
| 0 | Vatandaşlar 2 cevaplı ve 1 cevapsız soru soruyor |
| 1 | Giriş yapmadan `/admin/sss` → giriş sayfasına yönlendirme (`next` parametresiyle) |
| 2 | Yanlış şifre → hata mesajı; kullanıcı adı alanı boşalmıyor |
| 3 | Doğru şifre → istenen sayfaya (`/admin/sss`) dönüş; giriş yapmışken giriş sayfası panele yönlendiriyor |
| 4 | İstatistikler: toplam soru sayısı, grafik alanları, yerel Chart.js, cevaplanamayan soru ve “SSS olarak ekle” bağlantısı |
| 5 | “SSS olarak ekle” formu soruyu dolu getiriyor. Eksik alanla gönderim hata veriyor, eksiksiz gönderimle kayıt ekleniyor ve **chatbot artık cevaplıyor**. |
| 6 | Düzenleme → chatbot güncel cevabı veriyor |
| 7 | Silme → chatbot artık eşleştirmiyor; olmayan kaydı silme hata mesajı veriyor |
| 8 | Talep: Beklemede → İşlemde → Tamamlandı, durum filtreleri doğru; olmayan talep hata veriyor; istatistik kartı güncelleniyor |
| 9 | Sohbet geçmişinde “cevaplanamayanlar” filtresi |
| 10 | Çıkış → admin sayfaları tekrar kilitleniyor |

### `tests/test_guvenlik_ve_hatalar.py` – Güvenlik, hata yönetimi ve uç durumlar (52 test)

Bu dosya, [proje analizinde](proje_analizi.md) bulunan sorunların düzeltildiğini kanıtlar ve tekrar ortaya çıkmalarını önler.

| Konu | Testler | Neyi doğrular? |
|---|---|---|
| Oturum anahtarı | `test_secret_key_is_not_a_public_value`, `test_public_placeholder_secret_key_is_ignored`, `test_custom_secret_key_from_env_is_used` | Anahtar herkese açık bir değer değil; örnek değer yok sayılıyor; üretilen anahtar dosyada saklanıp tekrar kullanılıyor |
| **Sahte admin çerezi** | `test_session_cookie_signed_with_old_public_key_is_rejected` | Eski sürümdeki herkese açık anahtarla imzalanmış çerez panele **giremiyor** |
| Debug modu | `test_debug_mode_is_off_by_default` | Varsayılan olarak kapalı |
| Başlık ve çerez | `test_security_headers_are_set`, `test_session_cookie_flags_and_lifetime` | `X-Frame-Options`, `nosniff`, `Referrer-Policy`; çerez `HttpOnly`, `SameSite=Lax`, süreli |
| Admin hesabı | `test_changing_admin_username_removes_old_account`, `test_session_of_deleted_admin_is_invalidated` | Kullanıcı adı değişince eski `admin` hesabı siliniyor; silinen hesabın oturumu geçersiz |
| Giriş sınırı | `test_login_is_locked_after_too_many_failures` | 5 hatadan sonra doğru şifre bile 429; kilit süresi dolunca giriş açılıyor |
| Şifre uyarısı | `test_default_password_warning_banner`, `test_no_warning_banner_with_custom_password` | Uyarı sadece `admin123` kullanılırken görünüyor |
| SSS formu | `test_faq_form_rejects_too_long_fields` | Sunucu tarafı uzunluk sınırı |
| Bozuk istekler (8) | `test_non_object_json_body_returns_400_not_500` | Liste, metin, sayı, bozuk JSON gövdeleri iki API'de de 500 değil 400 |
| API hataları | `test_too_large_request_body_returns_json_413`, `test_unknown_api_url_returns_json_404`, `test_unexpected_error_returns_json_without_traceback` | 413/404/500 cevapları Türkçe JSON; iç hata ayrıntısı sızmıyor |
| Uç durum mesajları (4) | `test_edge_case_messages_do_not_crash` | Sadece noktalama, emoji, İngilizce soru, boşluklu tek harf |
| Telefon (9) | `test_valid_phone_numbers_are_accepted`, `test_invalid_phone_numbers_are_rejected` | `+90 555…`, `0 (850)…` kabul; `-------`, `12345`, harfli numara red |
| Alan türü ve uzunluğu (8) | `test_non_string_ticket_fields_are_rejected`, `test_ticket_field_length_limits`, `test_single_character_name_is_rejected` | Liste/sayı değerler red; 100/150/2000 sınırlarının tam sınırda kabul, bir fazlasında red edilmesi |
| XSS | `test_xss_payloads_are_escaped_in_admin_pages` | `<script>`, `<img onerror>`, `<svg onload>` admin sayfalarında kaçışlanıyor |
| Açılış hataları | `test_corrupt_seed_file_gives_clear_error`, `test_seed_file_with_missing_fields_gives_clear_error`, `test_missing_seed_file_gives_clear_error`, `test_corrupt_database_file_gives_clear_error`, `test_invalid_numeric_env_setting_gives_clear_error` | Python hata çıktısı yerine çözüm öneren Türkçe mesaj |
| Model güncelleme | `test_matcher_refit_swaps_model_in_one_step` | SSS değişince yeni model tek adımda devreye giriyor, eski model bozulmuyor |

### `tests/test_teslim_oncesi.py` – Teslim öncesi kontroller (14 test)

| Konu | Testler | Neyi doğrular? |
|---|---|---|
| İsim | `test_no_file_mentions_old_city_name`, `test_pages_use_belediye_chatbot_name` | Projedeki hiçbir metin dosyasında eski şehir adı yok; sayfa başlığı ve selamlama “Belediye Chatbot” |
| Favicon | `test_favicon_ico_is_served`, `test_favicon_svg_is_served`, `test_pages_link_the_favicon` | `/favicon.ico` 200 ve geçerli ICO; SVG simge sunuluyor; ana sayfa, giriş ve admin sayfalarında simge bağlantısı var |
| Talep red nedeni | `test_rejected_ticket_explains_each_field`, `test_rejected_ticket_logs_field_names_but_not_values`, `test_phone_with_dots_is_accepted` | Her alan için Türkçe neden; konsola alan adları yazılıyor ama kişisel veri yazılmıyor; `0555.123.45.67` kabul |
| Aydınlatma notu | `test_ticket_form_script_has_privacy_note_and_required_marks` | Toplanan veriler, demo uyarısı, zorunlu alan ipucu ve hata özeti formda |
| Sunucu | `test_run_server_uses_waitress_when_debug_is_off`, `test_request_log_line_format` | Debug kapalıyken waitress kullanılıyor; istek satırı `[SS:DD:ss] POST /api/talep 400` biçiminde |
| `.bat` dosyaları (3) | `test_bat_files_switch_console_to_utf8` | BOM yok, CRLF satır sonu, ilk satırlar `@echo off` + `chcp 65001 >nul` |

---

## 2. Doğruluk ölçümü

```powershell
.\venv\Scripts\python.exe scripts\dogruluk_olcumu.py
```

| Soru seti | Öncesi | Sonrası |
|---|---|---|
| İlgili sorular (40) | 40/40 | 40/40 |
| Alakasız sorular (15) | 12/15 | 15/15 |
| Kontrol seti – ayarlamada kullanılmadı (20) | 13/20 | **15/20** |

Soru soru skorlar ve yorum: [dogruluk_olcumu.md](dogruluk_olcumu.md)

---

## 3. Uçtan uca manuel senaryolar (demo akışı)

**Hazırlık:** `basla.bat` penceresi açıksa kapatın → **`sifirla.bat`** (E + Enter) → **`basla.bat`**

| # | Senaryo | Adımlar | Beklenen sonuç | Sonuç |
|---|---|---|---|---|
| M1 | Sohbeti açma | Ana sayfada sağ alttaki balona tıkla | Pencere açılır, karşılama mesajı ve 10 kategori butonu görünür | ✅ |
| M2 | Bilinen soru | `çöpler hangi gün toplanıyor` yaz | Temizlik İşleri cevabı ve altında birim bilgisi | ✅ |
| M3 | Türkçe karaktersiz yazım | `faturami nerden oderim` yaz | Su faturası ödeme cevabı (skor ≈ 0.48) | ✅ |
| M4 | Hızlı soru (sayfa) | “Hızlı Sorular” bölümünde *Nikah başvurusu için hangi belgeler gerekiyor?* sorusuna tıkla | Sohbet açılır, nikah belgeleri cevabı gelir | ✅ |
| M5 | Hızlı soru (sohbet içi) | Sohbette **Ulaşım** → *Öğrenci kartı…* sorusu | Öğrenci kartı cevabı gelir | ✅ |
| M6 | Selamlama | `merhaba` yaz | Asistan kendini tanıtır | ✅ |
| M7 | Kapsam dışı soru | `elektrik faturamı nasıl öderim` yaz | *“Bu konu belediyemizin hizmet alanı dışında görünüyor”*, Beyaz Masa, Evet/Hayır butonları | ✅ |
| M8 | Cevapsız soru | `sokak lambası yanmıyor` yaz | *“Net bir cevap bulamadım”*, Beyaz Masa'ya yönlendirme, Evet/Hayır | ✅ |
| M9 | Talep formu doğrulama | M8'de **Evet, talep oluştur** → boş haliyle **Gönder** | Konu ve birim önceden dolu; *“Ad soyad zorunludur”*, *“Açıklama zorunludur”* | ✅ |
| M10 | Talep oluşturma | Ad soyad, telefon, açıklama doldur → **Gönder** | *“Talebiniz #1 numarasıyla … iletildi”*, form kapanır | ✅ |
| M11 | Mobil görünüm | Tarayıcıyı telefon genişliğine (≈390px) getir | Sohbet tam ekran; ana sayfa ve admin sayfalarında yatay kaydırma yok | ✅ |
| M12 | Admin koruması | Oturum açmadan `/admin/sss` | Giriş sayfasına yönlendirilir | ✅ (otomatik test) |
| M13 | Admin girişi | `/admin` → `admin` / `admin123` | İstatistikler sayfası açılır | ✅ (otomatik test) |
| M14 | İstatistik grafikleri | M2–M10 sonrasında istatistik sayfası | 4 özet kartı dolu; 3 grafik yerel Chart.js 4.4.1 ile çiziliyor | ✅ |
| M15 | Talep durumu | **Talep / Şikayetler** → #1 → *İşlemde* seç → **Kaydet** | Onay mesajı; durum kutusu mavi (*İşlemde*), yeşil (*Tamamlandı*), turuncu (*Beklemede*) | ✅ |
| M18 | Uzun soruyla talep | 150 karakterden uzun bir soru yaz → **Evet, talep oluştur** | Konu 150 karakterde “…” ile kısalır, sorunun tamamı Açıklama alanına yazılır; gönderim hatasız | ✅ (tarayıcıda, 15.09.2026) |
| M19 | XSS denemesi | Sohbete `<img src=x onerror="alert(1)">` yaz | Metin olduğu gibi görünür, uyarı penceresi açılmaz | ✅ (tarayıcıda, 15.09.2026) |
| M20 | Selamlama sonrası konular | `merhaba` yaz | Cevabın altında konu butonları çıkar | ✅ (tarayıcıda, 15.09.2026) |
| M21 | Talep red nedeni ve düzeltme | Menüden **Talep / Şikayet** → Telefon `0555 12`, Açıklama boş → **Gönder** → sonra telefonu `0555 123 45 67` yap, açıklama yaz → **Gönder** | İlk gönderimde **400**: Telefon ve Açıklama kırmızı, altında neden, özet *“Lütfen işaretli alanları düzeltin: Açıklama, Telefon.”*, imleç Açıklama'da; konsolda `Talep reddedildi, hatalı alanlar: aciklama, telefon`. Düzeltince **201** ve talep numarası | ✅ (tarayıcıda, 15.09.2026) |
| M22 | Aydınlatma notu ve varsayılan birim | Menüden talep formunu aç | Formun altında aydınlatma notu; İlgili Birim varsayılanı *Beyaz Masa*; zorunlu alanlarda `*` | ✅ (tarayıcıda, 15.09.2026) |
| M23 | Sekme simgesi | Ana sayfayı ve admin girişini aç | Sekmede sohbet balonu simgesi; konsolda `GET /favicon.ico 200` (404 yok) | ✅ (15.09.2026) |
| M16 | Cevapsız sorudan SSS | İstatistikler → *sokak lambası yanmıyor* → **SSS olarak ekle** → formu doldur → kaydet → sohbette aynı soruyu sor | Soru alanı dolu gelir; kayıt sonrası chatbot cevap verir | ✅ (otomatik test: `test_admin_full_walkthrough`) |
| M17 | SSS düzenle / sil | **SSS Yönetimi** → Düzenle → kaydet; Sil → onayla | Başarı mesajları; chatbot güncel cevabı verir / artık vermez | ✅ (otomatik test) |

> **Not:** M12, M13, M16 ve M17 senaryolarının tarayıcıda şifre girilerek yapılan kısmı otomatik testlerle doğrulandı. Admin sayfalarının görünümü (hata/başarı mesajları, dolu form, durum renkleri, grafikler, mobil taşma) test verisiyle oluşturulan sayfa kopyalarında tarayıcıda kontrol edildi. **Sunumdan önce admin panelini bir kez kendiniz gezin.**

---

## 4. Kurulum ve çalıştırma testleri

| # | Test | Nasıl yapıldı? | Sonuç |
|---|---|---|---|
| K1 | `basla.bat` aktivasyon olmadan açılıyor | Yeni kabukta `basla.bat` çalıştırıldı, `/`, `/api/chat`, `/admin/giris`, `chart.umd.min.js` adreslerine istek atıldı | ✅ Hepsi 200 |
| K2 | `.env` olmadan çalışma | `.env` dosyası yokken K1 tekrarlandı | ✅ Varsayılan ayarlarla açıldı |
| K3 | Veritabanı yoksa oluşturma | `chatbot.db` silinip `basla.bat` çalıştırıldı | ✅ 70 SSS ile yeniden oluştu |
| K4 | **GitHub'dan yeni indirilmiş kopya** | Depo, `venv` ve veritabanı olmayan boş bir klasöre klonlandı; `basla.bat` çalıştırıldı | ✅ Python'u buldu, venv oluşturdu, paketleri yükledi, uygulama 200 döndü |
| K5 | `sifirla.bat` | `E` onayıyla çalıştırıldı | ✅ faq: 70, chat_log: 0, talep: 0 |
| K6 | `sifirla.bat` iptal | `E` dışında bir cevap verildi | ✅ “İşlem iptal edildi”, veritabanı silinmedi |
| K7 | `testleri_calistir.bat` | Çalıştırıldı | ✅ 122 passed (taşımadan hemen sonra, düzeltmelerden önce: 56 passed) |
| K9 | **Klasör taşıma** | Proje `C:\Projects\belediye-chatbot` konumuna taşındı, eski venv silindi, `basla.bat` venv'i yeniden kurdu | ✅ Git geçmişi (11 commit) ve remote sağlam, sayfalar 200, `sifirla.bat` çalışıyor |
| K10 | Üretim sunucusuyla başlangıç | `basla.bat` konsol çıktısı | ✅ `Sunucu: waitress`, *development server* uyarısı yok, varsayılan şifre uyarısı ve istek satırları görünüyor |
| K11 | Türkçe `.bat` çıktıları | Üç `.bat` dosyası çalıştırılıp ham çıktı UTF-8 olarak incelendi | ✅ *“başlatılıyor”, “tuşlarına”, “Veritabanı yeniden oluşturuldu”* doğru; komut satırı ayrıştırma hatası yok |
| K8 | `.bat` satır sonları | Klonlanan kopyada kontrol edildi | ✅ CRLF (`.gitattributes` ile sabitlendi) |
