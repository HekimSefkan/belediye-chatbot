# Kullanıcı Kılavuzu

> Bu proje bir staj çalışmasıdır. İçerdiği tüm veriler kurgusal demo verisidir, kurumun resmi verisi değildir.

Bu kılavuz iki bölümden oluşur: **Vatandaş** kullanımı ve **Yönetici (admin)** kullanımı.

---

## Bölüm 1 – Vatandaş

### 1.1 Sohbeti başlatma

1. Tarayıcıda **http://127.0.0.1:5000** adresini açın.
2. Sağ alt köşedeki yuvarlak **sohbet balonuna** ya da sayfadaki **Asistanla Konuş** butonuna tıklayın.
3. Açılan pencerede asistan sizi karşılar ve konu başlıklarını buton olarak gösterir.

Telefonda sohbet penceresi tüm ekranı kaplar. Pencereyi sağ üstteki **×** butonuyla ya da klavyede **Esc** tuşuyla kapatabilirsiniz.

### 1.2 Soru sorma

- Alt kısımdaki kutuya sorunuzu **günlük dilde** yazıp **Enter** tuşuna veya gönder butonuna basın.
  - Örnek: *“Su faturamı nasıl ödeyebilirim?”*, *“nikah için hangi belgeler lazım”*, *“cop toplama gunleri”*
- Türkçe karakter kullanmak zorunlu değildir.
- Cevabın altında hangi **kategori** ve **birim** ile ilgili olduğu yazar.

### 1.3 Hızlı sorular

- Ana sayfadaki **Hızlı Sorular** bölümünde her kategorinin sık sorulan soruları listelenir. Bir soruya tıklamanız, o soruyu sohbete göndermeniz için yeterlidir.
- Sohbet penceresindeki **Hızlı Sorular** butonu önce konu başlıklarını, konu seçilince de o konunun sorularını gösterir.

### 1.4 Cevap bulunamazsa

Asistan sorunuza uygun bir cevap bulamazsa:

1. *“Bu konuda net bir cevap bulamadım”* der ve sizi **ilgili birime** (bilinmiyorsa Beyaz Masa'ya) yönlendirir.
2. Varsa **“Şunlardan birini mi sormak istediniz?”** başlığıyla benzer soruları gösterir. Birine tıklayarak cevabını görebilirsiniz.
3. **Evet, talep oluştur** veya **Hayır, teşekkürler** seçeneklerini sunar.

### 1.5 Talep / şikayet oluşturma

Talep formunu üç şekilde açabilirsiniz:
- Cevap bulunamadığında **Evet, talep oluştur** butonuyla. Bu durumda konu ve birim otomatik doldurulur.
- Sohbet penceresindeki **Talep / Şikayet Oluştur** butonuyla.
- Sayfanın üstündeki **Talep / Şikayet** bağlantısıyla.

Formu doldurun:

| Alan | Zorunlu mu? | İpucu |
|---|---|---|
| Ad Soyad | Evet | |
| Telefon | Hayır | Size dönüş yapılabilmesi için önerilir |
| İlgili Birim | Evet | Listeden seçin, emin değilseniz Beyaz Masa'yı seçin |
| Konu | Evet | Kısa bir başlık |
| Açıklama | Evet | **Adres ve ayrıntıları** yazmanız talebin hızlı çözülmesini sağlar |

**Gönder** butonuna bastığınızda talebiniz kaydedilir ve size bir **talep numarası** verilir (örn. *#12*). Eksik veya hatalı alanlar kırmızı renkle ve açıklamasıyla gösterilir.

---

## Bölüm 2 – Yönetici (Admin)

### 2.1 Giriş

1. **http://127.0.0.1:5000/admin** adresini açın. Ana sayfanın en altındaki **Yönetici Girişi** bağlantısını da kullanabilirsiniz.
2. Kullanıcı adı ve şifrenizi girin. Varsayılan bilgiler `admin` / `admin123` şeklindedir. **İlk kurulumda `.env` dosyasından mutlaka değiştirin.**
3. Çıkmak için sol menünün altındaki **Çıkış Yap** butonunu kullanın.

> Şifreyi değiştirmek için `.env` dosyasındaki `ADMIN_PASSWORD` değerini güncelleyip uygulamayı yeniden başlatmanız yeterlidir.

### 2.2 İstatistikler

Girişten sonra ilk açılan sayfadır.

- **Özet kartları:** toplam soru sayısı, cevaplanamayan soru oranı, talep sayıları (durumlara göre), SSS kayıt sayısı. Cevaplanamayan oranı %30'u geçerse kart turuncu renkle vurgulanır.
- **Grafikler:** en çok sorulan kategoriler, cevaplanan/cevaplanamayan oranı, son 7 günün mesaj sayısı.
- **Son cevaplanamayan sorular:** chatbotun cevap veremediği mesajlar. Bir satırdaki **SSS olarak ekle** bağlantısı, soru alanı doldurulmuş olarak yeni SSS formunu açar.

### 2.3 SSS yönetimi

**Listeleme ve arama**
- Üstteki açılır menüden kategori seçip ya da arama kutusuna kelime yazıp **Filtrele** butonuna basın.
- Filtreyi kaldırmak için **Temizle** bağlantısına tıklayın.

**Yeni SSS ekleme**
1. **+ Yeni SSS** butonuna tıklayın.
2. **Kategori** ve **Sorumlu departman** alanlarında mevcut değerler öneri olarak çıkar. İsterseniz yeni bir değer de yazabilirsiniz.
3. **Soru** alanına sorunun vatandaşın soracağı şekilde yazılmış hâlini girin.
4. **Cevap** alanına vatandaşa gösterilecek metni girin.
5. **Anahtar kelimeler** alanına aynı konunun farklı ifade biçimlerini ekleyin (örn. *fatura ödeme borç vezne*). Bu alan eşleşme başarısını belirgin şekilde artırır.
6. **SSS Ekle** butonuna basın. Chatbot yeni soruyu **hemen** kullanmaya başlar.

**Düzenleme / silme**
- Satırdaki **Düzenle** butonu formu mevcut değerlerle açar.
- **Sil** butonu onay sorar. Onaylarsanız kayıt kalıcı olarak silinir.

### 2.4 Talep / şikayetler

- Üstteki sekmelerle **Tümü / Beklemede / İşlemde / Tamamlandı** filtrelerini kullanın.
- Her satırın **Durum** kutusundan yeni durumu seçtiğinizde değişiklik otomatik olarak kaydedilir ve sayfanın üstünde onay mesajı görünür.
- Önerilen iş akışı: **Beklemede** (yeni gelen) → **İşlemde** (ilgili birime iletildi) → **Tamamlandı**.

### 2.5 Sohbet geçmişi

- Son 200 mesaj; tarih, vatandaş mesajı, bot cevabı, kategori, benzerlik skoru ve sonuç bilgileriyle listelenir.
- **Cevaplanamayanlar** sekmesi, SSS veritabanında eksik olan konuları bulmak için kullanılır.
- Skoru 0.30–0.35 arasında kalan mesajlar genellikle mevcut bir SSS'ye çok yakındır. Bu SSS'nin anahtar kelimelerine yeni ifadeler eklemek çoğu zaman yeterli olur.

---

## Sık karşılaşılan sorunlar

| Sorun | Çözüm |
|---|---|
| `python` komutu bulunamadı | Python 3.11+ kurun ve kurulumda **Add python.exe to PATH** seçeneğini işaretleyin |
| PowerShell `activate` betiğini çalıştırmıyor | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` komutunu çalıştırın veya `venv\Scripts\python.exe app.py` ile başlatın |
| 5000 portu kullanımda | `.env` dosyasında `PORT=5001` yapın |
| Admin şifresini unuttum | `.env` dosyasında `ADMIN_PASSWORD` değerini değiştirip uygulamayı yeniden başlatın |
| Demo verilere geri dönmek istiyorum | Uygulamayı durdurun, `database/chatbot.db` dosyasını silin ve yeniden başlatın |
