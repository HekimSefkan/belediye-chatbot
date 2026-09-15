# Savunma Soruları ve Cevapları

> Bu proje bir staj çalışmasıdır. İçerdiği tüm veriler kurgusal demo verisidir, kurumun resmi verisi değildir.

Komisyonun veya danışman öğretmenin sorabileceği sorular ve kısa, savunulabilir cevapları. Cevapları ezberlemek yerine **mantığını** anlamak daha faydalıdır. Her cevabın sonunda, gerekirse gösterebileceğin dosya belirtilmiştir.

---

### 1. Neden TF-IDF kullandın?

Üç nedeni var:

- **Açıklanabilir:** Chatbot bir cevap verdiğinde bunun nedenini bir sayıyla (benzerlik skoru) gösterebiliyorum. Hangi kelimelerin eşleştiği de görülebiliyor. Kamu kurumunda vatandaşa verilen cevabın nedeninin izlenebilmesi önemli.
- **Hafif ve hızlı:** 70 soruluk bir bilgi tabanında cevap milisaniyeler içinde dönüyor. GPU veya güçlü sunucu gerekmiyor.
- **Veri ihtiyacı az:** Derin öğrenme modelleri binlerce etiketli örnek ister. TF-IDF sadece SSS listesiyle çalışıyor. Admin yeni soru eklediğinde model saniyeden kısa sürede yeniden eğitiliyor.

Stajyer ölçeğinde, 20 günde bitirilebilecek ve baştan sona anlatılabilecek bir yöntem olması da seçimde etkili oldu.
📄 `chatbot/matcher.py`

### 2. Neden yapay zeka API'si (ChatGPT, Claude vb.) kullanmadın?

- **Maliyet:** Bu API'ler mesaj başına ücretlidir. Proje şartlarında ücretli servis kullanılmaması istendi.
- **İnternet erişimi:** Belediye kurumsal ağında internet erişimi kısıtlı olabilir. Proje tamamen offline çalışıyor.
- **Kişisel veri (KVKK):** Vatandaş mesajları ad, adres, telefon içerebilir. Bunları yurt dışındaki bir şirketin sunucusuna göndermek KVKK açısından risklidir. Bu projede tüm veri belediyenin kendi bilgisayarında kalıyor.
- **Kontrol:** LLM'ler bazen var olmayan bilgi uydurabilir (halüsinasyon). Resmi bir kurumda yanlış ücret veya prosedür söylemek sorun olur. Bu sistem sadece belediyenin onayladığı SSS cevaplarını veriyor, kendi cümle üretmiyor.

Gelecekte isteğe bağlı bir katman olarak eklenebileceğini sınırlılıklar bölümünde belirttim.

### 3. Kök bulmayı (stemming) nasıl yaptın?

Türkçe eklemeli bir dil: *fatura, faturam, faturamı, faturası, faturanızı*. Bunların hepsinin aynı kelime olarak algılanması gerekiyor.

Kelimenin **ilk 5 harfini** aldım (F5 yöntemi): *faturamı → fatur*, *faturası → fatur*. Bu, Türkçe bilgi erişimi çalışmalarında kullanılan, basit ama etkili bir yöntem. Zemberek gibi tam bir morfolojik analizci Java tabanlı ve kurulumu karmaşık; stajyer projesi için gereksiz ağırlık getirirdi.

Dezavantajı: Bazen farklı kelimeler aynı köke düşebiliyor (*kesinti / kesin*). Testlerde bu önemli bir soruna yol açmadı.
📄 `chatbot/preprocessor.py` → `stem()` fonksiyonu, testi: `test_clean_text_same_root_for_different_suffixes`

### 4. Eşik değerini neden 0.35 seçtin?

Deneme yoluyla, ölçüme dayanarak seçtim:

- Doğru eşleşmesi gereken 40 farklı ifadede **en düşük skor 0.36** çıktı (*“trafik lambası bozuk”*). Eşiği 0.40 yapsaydım bu tür doğru cevapları kaybedecektim.
- Alakasız sorular çoğunlukla 0.00–0.32 arasında kaldı. 0.35, iki grubu ayıran makul bir sınır oldu.

Ayrıca **0.30–0.35** arası bir “emin değilim” bandı var. Bu bantta cevap verilmiyor ama vatandaş en yakın SSS'nin birimine yönlendiriliyor. Eşik `.env` dosyasından değiştirilebiliyor. Belediye gerçek verilerle kullandığında yeniden ayarlanabilir.
📄 `docs/dogruluk_olcumu.md`, `config.py`

### 5. Chatbot bir soruyu yanlış anlarsa ne oluyor? Bunu nasıl ölçtün?

Ölçmek için `scripts/dogruluk_olcumu.py` betiğini yazdım. Üç soru seti var: ilgili, alakasız ve **ayarlamada hiç kullanmadığım bir kontrol seti**. Kontrol setinde başarı %65'ten %75'e çıktı.

Hatalı cevabın etkisini azaltmak için:
- Her cevabın altında **hangi kategori ve birimden** geldiği yazıyor. Vatandaş yanlış konuda olduğunu fark edebiliyor.
- Cevap bulunamayan her soru kaydediliyor ve admin panelinde **“SSS olarak ekle”** bağlantısıyla bilgi tabanına ekleniyor. Sistem kullanıldıkça gelişiyor.

Yöntemin anlamı değil kelimeleri karşılaştırdığını açıkça biliyorum. Örneğin *“telefon faturamı ödemek istiyorum”* sorusu hâlâ su faturasıyla eşleşiyor. Bunu README'de sınırlılık olarak yazdım.

### 6. “Hava durumu” gibi alakasız soruları nasıl engelledin?

İki basit yöntemle:

1. **Stopword listesini genişlettim:** *durum, gün, zaman, olacak* gibi konu belirtmeyen kelimeleri çıkardım. Böylece *“hava durumu”* sorusu artık *“imar durum belgesi”* ile “durum” kelimesi üzerinden eşleşmiyor.
2. **Kapsam dışı kelime listesi ekledim:** *elektrik, doğalgaz, hastane, okul…* Bu kelimeler mesajda geçiyor ama eşleşen SSS'de geçmiyorsa eşleşmeyi reddediyorum. *“Doğalgaz faturası çok yüksek geldi”* sorusu 0.73 gibi yüksek bir skor almasına rağmen su faturası cevabını vermiyor.

Önce/sonra ölçümü `docs/dogruluk_olcumu.md` dosyasında.

### 7. Güvenlik için neler yaptın?

- **SQL injection:** Tüm sorgular parametreli (`?` yer tutucu). `x'); DROP TABLE faq; --` mesajının tabloyu silmediğini doğrulayan bir test var.
- **Şifre:** Admin şifresi veritabanında hash olarak saklanıyor (Werkzeug). Veritabanı ele geçirilse bile şifre okunamıyor.
- **CSRF:** Admin formlarında oturuma özel gizli token var. Başka bir sitenin, admin adına sahte form göndermesi engelleniyor.
- **XSS:** Vatandaş mesajları ekrana `textContent` ile yazılıyor. `<script>` yazılsa bile kod olarak çalışmıyor; bunu tarayıcıda da denedim.
- **Girdi doğrulama:** Alan türü, uzunluk sınırları, telefon formatı ve departman listesi sunucu tarafında kontrol ediliyor. İstek boyutu en fazla 64 KB.
- **Oturum:**
  - Oturum anahtarı her kurulumda rastgele üretiliyor.
  - 5 hatalı denemeden sonra giriş 5 dakika kilitleniyor.
  - Oturum 8 saat sonra kapanıyor.
- **Debug modu kapalı:** Hata olursa kullanıcıya kaynak kodu veya dosya yolu gösterilmiyor.

**Analizde bulduğum kritik açık:** İlk sürümde oturum anahtarı kodda sabit yazılıydı ve kod GitHub'da herkese açıktı. Bu anahtarla sahte bir çerez imzalayıp **şifre girmeden** admin paneline girilebildiğini kendim denedim ve gösterdim. Anahtarı rastgele üretilen, GitHub'a yüklenmeyen bir dosyaya taşıdım ve bunu doğrulayan bir test yazdım. Bu bana “güvenliği iddia etmek değil, denemek gerekir” dersini verdi.

📄 `tests/test_guvenlik_ve_hatalar.py`, `docs/proje_analizi.md`

### 8. Neden SQLite? Belediye gerçekten kullansa yeterli olur mu?

Demo ve pilot kullanım için yeterli. Kurulum gerektirmiyor, tek dosya, yedeklemesi kopyalamak kadar kolay. SQLite okuma ağırlıklı ve orta trafikli uygulamalarda sorunsuz çalışır.

Çok sayıda eş zamanlı kullanıcı olursa PostgreSQL gibi bir sunucu veritabanına geçmek gerekir. Sorgular standart SQL ile yazıldığı için geçiş mümkün. Ancak sorgular hem `database/db.py` hem de rota dosyalarında (`routes/`) bulunuyor; önce hepsinin tek bir veri erişim katmanında toplanması gerekir. Ayrıca gerçek yayında Flask'ın geliştirme sunucusu yerine Waitress gibi bir WSGI sunucusu kullanılmalı.

### 9. Projeyi nasıl test ettin?

Dört grupta:

1. **Birim testleri:** Ön işleme ve eşleştirme fonksiyonları (`tests/test_matcher.py`, 34)
2. **API ve entegrasyon testleri:** Uç noktalar, doğrulama, güvenlik (`tests/test_api.py`, 21)
3. **Uçtan uca senaryo testi:** Adminin giriş yapıp cevapsız bir sorudan SSS oluşturması, düzenlemesi, silmesi, talep durumunu güncellemesi ve çıkış yapması (`tests/test_admin_akisi.py`, 1)
4. **Güvenlik ve hata testleri:** Sahte oturum çerezi, bozuk istekler, emoji/İngilizce mesajlar, bozuk veritabanı dosyası gibi uç durumlar (`tests/test_guvenlik_ve_hatalar.py`, 52)

Toplam **108 test**; hepsi geçiyor. Son grup, projeyi baştan sona analiz ettiğimde bulduğum sorunların tekrar ortaya çıkmaması için eklendi. Testler geçici bir veritabanında çalışıyor. Bunlara ek olarak tarayıcıda masaüstü ve mobil görünümde manuel senaryoları uyguladım (`docs/test_senaryolari.md`).

### 10. Bu proje gerçekte belediyeye ne kazandırır? Nasıl geliştirilir?

**Kazanımlar:**
- Çağrı merkezi ve Beyaz Masa'ya gelen tekrarlayan soruların (çöp günleri, fatura ödeme, nikah belgeleri) bir kısmı otomatik cevaplanır. Personel karmaşık işlere zaman ayırır.
- 7/24 hizmet verir.
- Sohbet geçmişi, **vatandaşların en çok neyi merak ettiğini** gösteren bir veri kaynağı olur. Hangi konularda duyuru yapılması gerektiği anlaşılır.

**Geliştirme yönleri:**
- Gerçek belediye SSS'leriyle bilgi tabanının genişletilmesi (en etkili iyileştirme)
- Yazım hatası toleransı (Levenshtein mesafesi)
- Eş anlamlı kelime sözlüğü
- Anlamı dikkate alan, yerel çalışan bir kelime vektörü modeli
- Vatandaşın talep numarasıyla durum sorgulayabilmesi
- Belediye web sitesine ve e-belediyeye entegrasyon

---

## Kısa cevap kartı (sunumdan önce göz gezdir)

| Soru | Tek cümlelik cevap |
|---|---|
| Neden TF-IDF? | Açıklanabilir, hızlı, az veriyle çalışıyor ve offline. |
| Neden API yok? | Ücretli, internet ister, vatandaş verisini dışarı gönderir (KVKK) ve bilgi uydurabilir. |
| Kök bulma? | Kelimenin ilk 5 harfi (F5): *faturamı → fatur*. |
| Neden 0.35? | Doğru eşleşmelerin en düşüğü 0.36, alakasızlar çoğunlukla 0.32'nin altında. |
| En büyük zayıflık? | Anlamı değil kelimeleri karşılaştırıyor: *“telefon faturası”* hâlâ *“su faturası”* ile eşleşiyor. |
| Doğruluk? | Kontrol setinde %75. İlgili soruların hepsi doğru; alakasızların yarısı yanlış eşleşiyor. |
| Güvenlik? | Parametreli SQL, hash'li şifre, rastgele oturum anahtarı, giriş denemesi sınırı, CSRF token, XSS'e karşı textContent. |
| Test? | 108 otomatik test: birim, API, uçtan uca admin senaryosu, güvenlik ve hata durumları. |
| Bulduğun en ciddi hata? | Kodda sabit oturum anahtarı → şifresiz admin girişi. Kendim denedim, düzelttim, testle kanıtladım. |
