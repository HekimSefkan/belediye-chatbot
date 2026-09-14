# Test Senaryoları ve Sonuçları

> Bu proje bir staj çalışmasıdır. İçerdiği tüm veriler kurgusal demo verisidir, kurumun resmi verisi değildir.

Bu belge iki bölümden oluşur:

1. **Otomatik testler (pytest):** Kod değiştiğinde tek komutla tekrar çalıştırılabilir.
2. **Uçtan uca manuel senaryolar:** Sunum/demo sırasında tarayıcıda uygulanacak adımlar ve beklenen sonuçlar.

---

## 1. Otomatik testler

Çalıştırma (sanal ortam etkinken, proje klasöründe):

```powershell
pytest -v
```

**Sonuç (14.09.2026):** `48 passed`

### `tests/test_matcher.py` – Ön işleme ve eşleştirme (28 test)

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
| `test_unrelated_messages_are_below_threshold` (3 örnek) | Konu dışı mesajlar eşik altında kalıyor |
| `test_only_stopwords_returns_not_found` | Sadece bağlaçlardan oluşan mesaj eşleşmiyor |
| `test_empty_matcher_does_not_crash` | SSS tablosu boşken uygulama çökmüyor |
| `test_threshold_is_configurable` | Eşik değeri ayardan değiştirilebiliyor |
| `test_suggestions_respect_limit_and_min_score` | Öneri listesi en fazla 3 kayıt ve doğru kategori içeriyor |
| `test_greeting_response` | “Merhaba” mesajına selamlama cevabı veriliyor |
| `test_not_found_response_offers_ticket_and_default_department` | Cevap yoksa talep teklif ediliyor ve Beyaz Masa'ya yönlendiriliyor |
| `test_found_response_contains_department` | Bulunan cevapta departman bilgisi var |

### `tests/test_api.py` – API ve admin paneli (20 test)

| Test | Neyi doğrular? |
|---|---|
| `test_chat_returns_answer_for_known_question` | `/api/chat` bilinen soruya 200 ve doğru kategoriyle cevap veriyor |
| `test_chat_is_logged_to_database` | Mesaj, skor ve kategori `chat_log` tablosuna yazılıyor |
| `test_chat_unknown_question_offers_ticket` | Bilinmeyen soruda `offer_ticket: true` dönüyor, log'da `cevap_bulundu_mu = 0` |
| `test_chat_greeting` | Selamlama tipi cevap dönüyor |
| `test_chat_rejects_empty_message` | Boş mesaj, eksik alan ve JSON olmayan istek 400 dönüyor |
| `test_chat_rejects_too_long_message` | 500 karakterden uzun mesaj reddediliyor |
| `test_chat_sql_injection_text_is_stored_safely` | `x'); DROP TABLE faq; --` metni tabloyu silmiyor, metin olarak saklanıyor |
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

---

## 2. Uçtan uca manuel senaryolar (demo akışı)

**Hazırlık:** Temiz bir demo için uygulamayı durdurun, `database/chatbot.db` dosyasını silin ve `python app.py` ile yeniden başlatın.

| # | Senaryo | Adımlar | Beklenen sonuç | Sonuç |
|---|---|---|---|---|
| M1 | Sohbeti açma | Ana sayfada sağ alttaki balona tıkla | Pencere açılır, karşılama mesajı ve 10 kategori butonu görünür | ✅ |
| M2 | Bilinen soru | `çöpler hangi gün toplanıyor` yaz | Temizlik İşleri cevabı, altında birim bilgisi (skor ≈ 0.50) | ✅ |
| M3 | Türkçe karaktersiz yazım | `faturami nerden oderim` yaz | Su faturası ödeme cevabı (skor ≈ 0.48) | ✅ |
| M4 | Hızlı soru (sayfa) | “Hızlı Sorular” bölümünde *Nikah başvurusu için hangi belgeler gerekiyor?* sorusuna tıkla | Sohbet açılır, nikah belgeleri cevabı gelir (skor ≈ 0.83) | ✅ |
| M5 | Hızlı soru (sohbet içi) | Sohbette **Hızlı Sorular** → **Ulaşım** → bir soru seç | Seçilen sorunun cevabı gelir | ✅ |
| M6 | Selamlama | `merhaba` yaz | Asistan kendini tanıtır | ✅ |
| M7 | Cevapsız soru | `sokak lambası yanmıyor` yaz | “Net bir cevap bulamadım”, Beyaz Masa'ya yönlendirme, **Evet/Hayır** butonları | ✅ |
| M8 | Talep formu doğrulama | M7'de **Evet, talep oluştur** → boş haliyle **Gönder** | Konu ve birim önceden dolu. “Ad soyad zorunludur”, “Açıklama zorunludur” hataları | ✅ |
| M9 | Talep oluşturma | Ad soyad, telefon, açıklama doldur → **Gönder** | “Talebiniz #1 numarasıyla … iletildi” mesajı, form kapanır | ✅ |
| M10 | Mobil görünüm | Tarayıcıyı telefon genişliğine (≈375px) getir | Sohbet tam ekran açılır, yatay kaydırma olmaz | ✅ |
| M11 | Admin koruması | Oturum açmadan `/admin/sss` adresine git | Giriş sayfasına yönlendirilir | ✅ (otomatik test) |
| M12 | Admin girişi | `/admin` → `admin` / `admin123` | İstatistikler sayfası açılır | ✅ (otomatik test) |
| M13 | İstatistikler | M2–M9 sonrasında istatistik sayfasına bak | Toplam soru, cevaplanamayan oranı, kategori grafiği dolu | ✅ |
| M14 | Talep durumu | **Talep / Şikayetler** → #1 → durumu *İşlemde* yap | Onay mesajı, satır mavi renkli *İşlemde* olur | ✅ (otomatik test) |
| M15 | Chatbotu geliştirme | İstatistikler → “sokak lambası yanmıyor” → **SSS olarak ekle** → cevap, kategori, departman yaz → kaydet → sohbette aynı soruyu tekrar sor | Artık cevap bulunur | ✅ (otomatik test: `test_admin_faq_create_updates_chatbot`) |
| M16 | SSS silme | **SSS Yönetimi** → bir kaydı **Sil** → onayla | Kayıt listeden kalkar, chatbot artık o cevabı vermez | ✅ (otomatik test) |

---

## 3. Bilinen sınırlılıklar (testlerde gözlenen)

| Mesaj | Sonuç | Açıklama |
|---|---|---|
| `hava durumu nasıl olacak` | *İmar durum belgesi* ile eşleşiyor (0.50) | TF-IDF anlama değil kelime benzerliğine bakar. “durum” kelimesi ortak olduğu için yanlış eşleşme oluşur. |
| `bugün günlerden ne` | *Çöp toplama günleri* ile eşleşiyor | “gün” kelimesi ortak |

Bu tür durumlar sunumda **yöntemin sınırlılığı** olarak anlatılabilir. Çözüm önerileri: SSS kapsamının ve anahtar kelimelerin genişletilmesi, konu dışı sorular için “kara liste” kelimeleri ya da ileride anlamsal benzerlik (word embedding) kullanan bir model.
