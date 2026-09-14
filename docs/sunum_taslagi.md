# Sunum Taslağı – Vatandaş Hizmetleri Chatbotu

> Bu proje bir staj çalışmasıdır. İçerdiği tüm veriler kurgusal demo verisidir, kurumun resmi verisi değildir.

**Toplam süre:** yaklaşık 10–12 dakika sunum + 3–4 dakika canlı demo
**Slayt sayısı:** 10

**Sunumdan önce hazırlık:**
1. `sifirla.bat` dosyasını çalıştır (temiz veritabanı).
2. `basla.bat` dosyasını çalıştır, tarayıcıda ana sayfayı ve ikinci bir sekmede `/admin` giriş sayfasını aç.
3. İnternet bağlantısı gerekmez. Sunum bilgisayarında Python kurulu değilse `basla.bat` kurulum ister, bu yüzden **kendi bilgisayarını** kullan.

---

## Slayt 1 – Kapak

**Ekranda:**
- Vatandaş Hizmetleri Chatbotu
- Mardin Büyükşehir Belediyesi – Bilgi İşlem Dairesi Başkanlığı
- Zorunlu Yaz Stajı Bitirme Projesi
- `[Adın Soyadın]` · `[Bölüm / Sınıf]` · `[Tarih]`
- *Not: Projedeki tüm veriler kurgusal demo verisidir.*

**Konuşma notu:**
> “Merhaba, ben [ad]. Stajımı Mardin Büyükşehir Belediyesi Bilgi İşlem Dairesi'nde yaptım. Bugün staj süresince geliştirdiğim Vatandaş Hizmetleri Chatbotu'nu anlatacağım. Başlamadan belirteyim: Projede kullandığım soru-cevapların hepsi kurgusal, gerçek belediye verisi değil.”

---

## Slayt 2 – Problem

**Ekranda:**
- Belediyeye her gün aynı sorular geliyor:
  - “Su faturamı nasıl öderim?”
  - “Çöpler hangi gün toplanıyor?”
  - “Nikah için hangi belgeler lazım?”
- Sonuç: Çağrı merkezi yükü, mesai dışında bilgiye ulaşamama, yanlış birime başvurma

**Konuşma notu:**
> “Belediyeler telefonla, Beyaz Masa'dan ve CİMER'den çok sayıda soru alıyor. Bunların önemli bir kısmının cevabı hep aynı. Personel bu soruları tek tek cevaplıyor, vatandaş da mesai dışında bilgiye ulaşamıyor. Ayrıca vatandaş çoğu zaman hangi birime gitmesi gerektiğini bilmiyor.”

---

## Slayt 3 – Amaç ve Kısıtlar

**Ekranda:**

| Amaç | Kısıt |
|---|---|
| Sık soruları 7/24 otomatik yanıtlamak | Ücretli API yok |
| Cevap yoksa doğru birime yönlendirmek | İnternet olmadan çalışmalı |
| Talep/şikayet kaydı almak | Tek stajyer, 20 iş günü |
| Personelin bilgi tabanını kolayca güncellemesi | Kod anlaşılır ve savunulabilir olmalı |

**Konuşma notu:**
> “Amacım bu tekrarlayan soruları otomatik yanıtlayan bir sistem yapmaktı. Ama bazı kısıtlarım vardı: Kurum ağında internet kısıtlı olabileceği için sistem offline çalışmalıydı, ücretli bir yapay zeka servisi kullanılmamalıydı ve 20 iş gününde tek başıma bitirebilmeliydim. Bu kısıtlar teknoloji seçimimi doğrudan belirledi.”

---

## Slayt 4 – Kullanılan Teknolojiler

**Ekranda:** (logolar veya ikonlarla)
- **Backend:** Python + Flask
- **Veritabanı:** SQLite
- **Doğal dil eşleştirme:** scikit-learn (TF-IDF + cosine similarity)
- **Arayüz:** HTML, CSS, JavaScript (framework yok)
- **Grafikler:** Chart.js (yerel dosya)
- **Test:** pytest · **Sürüm kontrolü:** Git / GitHub

**Konuşma notu:**
> “Backend için hafif ve öğrenmesi kolay olduğu için Flask'ı seçtim. Veritabanı olarak kurulum gerektirmeyen SQLite'ı kullandım. Chatbotun beyni scikit-learn kütüphanesindeki TF-IDF yöntemi. Arayüzde hiçbir framework kullanmadım; her satırı açıklayabilmek istedim. Grafik kütüphanesini bile internetten değil projenin içinden yüklüyorum.”

---

## Slayt 5 – Sistem Mimarisi

**Ekranda:** `docs/mimari_diyagram.md` → “Genel yapı” diyagramı (Tarayıcı → Flask → Chatbot modülü → SQLite)

**Konuşma notu:**
> “Sistem üç katmandan oluşuyor. Vatandaş ve yönetici tarayıcıdan bağlanıyor. Flask sunucusu istekleri karşılıyor. Vatandaşın mesajı chatbot modülüne gidiyor; bu modül metni temizliyor, SSS'lerle karşılaştırıyor ve cevabı üretiyor. Tüm SSS'ler, talepler ve sohbet geçmişi SQLite veritabanında tutuluyor. Model uygulama açılırken bir kez eğitiliyor. Yönetici yeni bir soru eklediğinde otomatik yeniden eğitiliyor.”

---

## Slayt 6 – Chatbot Nasıl Düşünüyor?

**Ekranda:**
```
"Su faturamı nasıl ödeyebilirim?"
   ↓ 1. Temizleme   → küçük harf, ç→c, noktalama, "nasıl" atılır
   ↓ 2. Kök bulma   → faturamı → fatur   (ilk 5 harf)
"su fatur odeye"
   ↓ 3. TF-IDF      → kelimelere önem puanı
   ↓ 4. Benzerlik   → 70 SSS ile karşılaştır
En yakın: "Su faturamı nasıl ödeyebilirim?"  skor: 0.66
   ↓ 5. Skor ≥ 0.35 → cevabı göster
```

**Konuşma notu:**
> “Chatbotun nasıl çalıştığını bir örnekle anlatayım. Önce mesajı temizliyorum: küçük harfe çeviriyorum, Türkçe karakterleri sadeleştiriyorum, ‘nasıl’ gibi anlam taşımayan kelimeleri atıyorum. Türkçe eklemeli bir dil olduğu için ‘faturamı’ ile ‘faturası’nın aynı kelime olduğunu anlaması gerekiyor; bunun için kelimenin ilk 5 harfini alıyorum. Sonra TF-IDF ile her kelimeye bir önem puanı veriyorum: ‘iskan’ gibi nadir kelimeler önemli, ‘belediye’ gibi her yerde geçenler önemsiz. Son olarak mesajı 70 soruyla karşılaştırıp en benzerini buluyorum. Skor 0.35'in üzerindeyse cevabı gösteriyorum, altındaysa vatandaşı ilgili birime yönlendirip talep oluşturmayı teklif ediyorum.”

---

## Slayt 7 – Veritabanı ve Admin Paneli

**Ekranda:**
- Sol: 4 tablo (faq, talep_sikayet, chat_log, admin)
- Sağ: Admin paneli ekran görüntüsü (istatistik grafikleri)
- Öne çıkan özellik: **Cevaplanamayan soru → “SSS olarak ekle” → chatbot artık cevaplıyor**

**Konuşma notu:**
> “Veritabanında dört tablo var: soru-cevaplar, talepler, sohbet geçmişi ve yönetici hesabı. Admin panelinde personel soruları ekleyip düzenleyebiliyor, talepleri takip edebiliyor ve grafiklerle hangi konuların en çok sorulduğunu görebiliyor. En sevdiğim özellik şu: Chatbot bir soruya cevap veremezse bu soru panelde listeleniyor. Personel tek tıkla bunu SSS'ye ekliyor ve chatbot bir sonraki sefere cevap verebiliyor. Yani sistem kullanıldıkça gelişiyor.”

---

## Slayt 8 – CANLI DEMO

**Ekranda:** “Canlı Demo” başlığı (tarayıcıya geç)

**Demo akışı (3–4 dakika):**
1. Balona tıkla → `çöpler hangi gün toplanıyor` → cevap ve birim bilgisi
2. `faturami nerden oderim` → *“Türkçe karakter kullanmasam da anlıyor”*
3. `elektrik faturamı nasıl öderim` → *“Kapsam dışı konuları tanıyor, su faturası cevabı vermiyor”*
4. `sokak lambası yanmıyor` → cevap yok → **Evet, talep oluştur** → formu doldur → talep numarası
5. Admin sekmesi → giriş → **İstatistikler** (grafikler) → **Talepler** (durumu *İşlemde* yap)
6. İstatistikler → “sokak lambası yanmıyor” → **SSS olarak ekle** → kaydet → sohbette aynı soruyu tekrar sor → **artık cevap veriyor**
7. (Zaman kalırsa) tarayıcıyı daraltarak mobil görünümü göster

**Konuşma notu:**
> “Şimdi sistemi canlı göstereyim…” *(Her adımda ne olduğunu kısaca söyle. Bir şey ters giderse sakin kal: “Bu da sınırlılıklardan birine iyi bir örnek” diyebilirsin.)*

---

## Slayt 9 – Test, Ölçüm ve Sınırlılıklar

**Ekranda:**
- **56 otomatik test**, hepsi başarılı (birim, API, uçtan uca admin senaryosu)
- **Güvenlik:** parametreli SQL, hash'li şifre, CSRF, XSS koruması
- **Doğruluk (ayarlamada kullanılmayan kontrol seti):** %65 → **%75**
- **Sınırlılık:** Anlamı değil kelimeleri karşılaştırıyor
  - “telefon faturamı ödemek istiyorum” → *su faturası* cevabı ❌

**Konuşma notu:**
> “Projeyi 56 otomatik testle doğruladım. Doğruluğu ölçmek için ayrıca bir betik yazdım. İlk sürümde ‘hava durumu nasıl olacak’ sorusu ‘imar durum belgesi’ ile eşleşiyordu, çünkü ikisinde de ‘durum’ kelimesi var. Stopword listesini genişletip kapsam dışı bir kelime listesi ekleyerek bunu düzelttim. Ayarlamada hiç kullanmadığım bir kontrol setinde başarı %65'ten %75'e çıktı. Ama dürüst olmam gerekirse, yöntem anlamı değil kelimeleri karşılaştırıyor: ‘telefon faturası’ sorusu hâlâ ‘su faturası’ ile eşleşiyor. Bu, TF-IDF'in doğal sınırı.”

---

## Slayt 10 – Sonuç ve Gelecek Çalışmalar

**Ekranda:**

**Sonuç**
- Uçtan uca çalışan, offline, ücretsiz bir vatandaş chatbotu
- Yönlendirme + talep kaydı + yönetim paneli
- Kurulum: tek dosyaya çift tıklama

**Geliştirilebilir**
- Gerçek belediye SSS'leriyle bilgi tabanı
- Yazım hatası toleransı, eş anlamlı sözlüğü
- Anlamsal benzerlik (yerel kelime vektörleri)
- Talep durumu sorgulama, e-belediye entegrasyonu

**Teşekkürler – Sorular?**
GitHub: `github.com/HekimSefkan/belediye-chatbot`

**Konuşma notu:**
> “Sonuç olarak internet ve ücretli servis gerektirmeden çalışan, vatandaşı doğru birime yönlendiren ve personelin kolayca yönetebildiği bir chatbot geliştirdim. Gerçek belediye verileriyle doldurulursa ve yazım hatası toleransı gibi özellikler eklenirse gerçek kullanıma yaklaşabilir. Bu projede bir yazılımı analizden teste kadar uçtan uca geliştirmeyi, doğal dil işlemenin temellerini ve web güvenliğini öğrendim. Dinlediğiniz için teşekkürler, sorularınızı alabilirim.”

---

## Sunum ipuçları

- Muhtemel sorular ve cevapları için: `docs/savunma_sorulari.md` (özellikle en alttaki **kısa cevap kartı**)
- Demo sırasında internet bağlantısını kapatıp göstermek, “offline çalışıyor” iddiasını güçlendirir.
- Kod göstermen istenirse en anlaşılır dosyalar: `chatbot/preprocessor.py` → `chatbot/matcher.py` → `routes/api_routes.py`
- Kötü senaryo planı: Demo çalışmazsa ekran görüntüleriyle devam et. Bu yüzden sunumdan önce ekran görüntülerini slaytlara ekle.
