# Doğruluk Ölçümü – İyileştirme Öncesi ve Sonrası

> Bu proje bir staj çalışmasıdır. İçerdiği tüm veriler kurgusal demo verisidir, kurumun resmi verisi değildir.

**Ölçüm tarihi:** 14.09.2026
**Betik:** `scripts/dogruluk_olcumu.py`. Veritabanı veya sunucu gerektirmez, istenildiği zaman tekrar çalıştırılabilir:

```powershell
.\venv\Scripts\python.exe scripts\dogruluk_olcumu.py
```

## Neden ölçüm yapıldı?

İlk sürümde bazı alakasız sorular, SSS'lerle **tek bir ortak kelime** paylaştığı için yanlış eşleşiyordu:

- *“hava durumu nasıl olacak”* → *“İmar durum belgesi nasıl alınır?”* (ortak kelime: **durum**)
- *“bugün günlerden ne”* → *“Mahallemde çöpler hangi günler toplanıyor?”* (ortak kelime: **gün**)
- *“doğalgaz kesintisi ne zaman bitecek”* → *“Mahallemde sular kesik, ne zaman gelecek?”* (ortak kelime: **kesinti**)

## Yapılan iyileştirmeler

Yöntem değiştirilmedi ve ek kütüphane eklenmedi. İki basit liste güncellendi:

1. **Stopword listesi genişletildi** (`chatbot/preprocessor.py`):
   - Genel zaman/durum kelimeleri: *durum, durumu, zaman, bugün, yarın, gün, günler…*
   - Konu belirtmeyen fiil kalıpları: *olacak, olsun, oluyor, bitecek…*
2. **Kapsam dışı kelime listesi eklendi** (`OUT_OF_SCOPE_WORDS`):
   - Liste: *elektrik, doğalgaz, hava, ehliyet, pasaport, hastane, eczane, okul, üniversite, askerlik, futbol, maç, dolar, euro, döviz, borsa*
   - Mesajda bu kelimelerden biri geçiyor ama **eşleşen SSS'de geçmiyorsa** eşleşme reddedilir ve vatandaşa *“Bu konu belediyemizin hizmet alanı dışında görünüyor”* denir.
   - Bir SSS bu kelimeyi gerçekten içeriyorsa engel uygulanmaz. Örneğin *pasaport* kelimesi yabancı uyruklu evlilik SSS'sinde geçtiği için o SSS eşleşmeye devam eder.

Eşik değeri (0.35) **değiştirilmedi**. Ölçümler, ilgili soruların en düşük skorunun 0.36 olduğunu gösterdi; eşiği yükseltmek doğru cevapları kaybettirirdi.

## Özet

| Soru seti | Soru sayısı | Öncesi | Sonrası |
|---|---|---|---|
| İlgili sorular – doğru kategoriye gitme | 40 | 40/40 (%100) | 40/40 (%100) |
| Alakasız sorular – reddetme | 15 | 12/15 (%80) | **15/15 (%100)** |
| **Kontrol seti** – ayarlamada hiç kullanılmadı | 20 | 13/20 (%65) | **15/20 (%75)** |

> **Dürüst yorum:** “Alakasız sorular” seti, listeler ayarlanırken kullanıldığı için %100 sonucu iyimserdir. Yöntemin **daha önce görmediği** sorulardaki gerçekçi başarısını **kontrol seti** gösterir. Kontrol setinde ilgili soruların hepsi doğru eşleşti. Alakasız 10 sorunun ise 5'i hâlâ yanlış eşleşiyor. Bu, kelime tabanlı yöntemin doğal sınırlılığıdır (bkz. README “Sınırlılıklar”).

---

## 1. İlgili sorular (40)

Seed verisindeki sorularla birebir aynı olmayan, vatandaşın farklı kelimelerle sorabileceği ifadeler.

| Mesaj | Beklenen kategori | Önce: skor | Sonra: skor | Sonuç (önce → sonra) |
|---|---|---|---|---|
| su faturası nasıl ödenir | Su ve Kanalizasyon | 0.48 | 0.48 | ✅ → ✅ |
| faturami nerden oderim | Su ve Kanalizasyon | 0.48 | 0.48 | ✅ → ✅ |
| suyumuz kesildi | Su ve Kanalizasyon | 0.38 | 0.41 | ✅ → ✅ |
| lağım taştı | Su ve Kanalizasyon | 0.45 | 0.45 | ✅ → ✅ |
| sayac bozuk | Su ve Kanalizasyon | 0.71 | 0.71 | ✅ → ✅ |
| imar durumu belgesi almak istiyorum | İmar ve Şehircilik | 0.68 | 0.57 | ✅ → ✅ |
| inşaat ruhsatı nasıl alınır | İmar ve Şehircilik | 0.56 | 0.56 | ✅ → ✅ |
| kaçak yapı ihbarı | İmar ve Şehircilik | 0.51 | 0.51 | ✅ → ✅ |
| iskan belgesi için ne gerekli | İmar ve Şehircilik | 0.43 | 0.43 | ✅ → ✅ |
| dükkan açmak için ruhsat | Zabıta | 0.56 | 0.56 | ✅ → ✅ |
| zabıtayı nasıl ararım | Zabıta | 0.64 | 0.64 | ✅ → ✅ |
| kaldırımı işgal eden dükkan | Zabıta | 0.63 | 0.63 | ✅ → ✅ |
| çöpler ne zaman toplanıyor | Temizlik İşleri | 0.42 | 0.57 | ✅ → ✅ |
| çöp kamyonu gelmedi | Temizlik İşleri | 0.52 | 0.59 | ✅ → ✅ |
| cop toplama gunleri | Temizlik İşleri | 0.78 | 0.70 | ✅ → ✅ |
| eski koltuğumu attırmak istiyorum | Temizlik İşleri | 0.55 | 0.55 | ✅ → ✅ |
| parktaki salıncak kırılmış | Park ve Bahçeler | 0.40 | 0.40 | ✅ → ✅ |
| ağaç budama talebi | Park ve Bahçeler | 0.59 | 0.59 | ✅ → ✅ |
| sokak köpekleri | Park ve Bahçeler | 0.63 | 0.63 | ✅ → ✅ |
| ücretsiz fidan dağıtımı | Park ve Bahçeler | 0.77 | 0.77 | ✅ → ✅ |
| evlenmek için gerekli belgeler | Evlilik/Nikah İşlemleri | 0.60 | 0.60 | ✅ → ✅ |
| nikah salonu rezervasyonu | Evlilik/Nikah İşlemleri | 0.84 | 0.84 | ✅ → ✅ |
| nikah şahidi kaç kişi olmalı | Evlilik/Nikah İşlemleri | 0.61 | 0.61 | ✅ → ✅ |
| nikah ücreti ne kadar | Evlilik/Nikah İşlemleri | 0.81 | 0.81 | ✅ → ✅ |
| emlak vergisi son ödeme tarihi | Emlak/Vergi | 0.76 | 0.86 | ✅ → ✅ |
| vergi borcumu sorgulamak istiyorum | Emlak/Vergi | 0.77 | 0.77 | ✅ → ✅ |
| borcumu taksitle ödeyebilir miyim | Emlak/Vergi | 0.49 | 0.49 | ✅ → ✅ |
| emekliler emlak vergisi öder mi | Emlak/Vergi | 0.68 | 0.68 | ✅ → ✅ |
| otobüs saatleri | Ulaşım | 0.65 | 0.65 | ✅ → ✅ |
| öğrenci kartı başvurusu | Ulaşım | 0.60 | 0.60 | ✅ → ✅ |
| otobüste çantamı unuttum | Ulaşım | 0.57 | 0.57 | ✅ → ✅ |
| trafik lambası bozuk | Ulaşım | 0.36 | 0.36 | ✅ → ✅ |
| kurslara kayıt | Kültür ve Sosyal İşler | 0.49 | 0.49 | ✅ → ✅ |
| sosyal yardım başvurusu | Kültür ve Sosyal İşler | 0.61 | 0.61 | ✅ → ✅ |
| kütüphane saatleri | Kültür ve Sosyal İşler | 0.64 | 0.67 | ✅ → ✅ |
| belediye etkinlik takvimi | Kültür ve Sosyal İşler | 0.59 | 0.59 | ✅ → ✅ |
| e-belediye şifremi unuttum | Bilgi İşlem/BİMER | 0.85 | 0.85 | ✅ → ✅ |
| wifi nerede var | Bilgi İşlem/BİMER | 0.39 | 0.39 | ✅ → ✅ |
| cimer başvurusu | Bilgi İşlem/BİMER | 0.62 | 0.62 | ✅ → ✅ |
| belediye sitesi açılmıyor | Bilgi İşlem/BİMER | 0.65 | 0.65 | ✅ → ✅ |

Stopword değişikliğinden sonra bazı skorlar yükseldi (*“çöpler ne zaman toplanıyor”* 0.42 → 0.57), bazıları hafifçe düştü (*“imar durumu belgesi…”* 0.68 → 0.57). Hiçbiri eşiğin altına inmedi.

## 2. Alakasız sorular (15)

| Mesaj | Önce: skor | Önce: sonuç | Sonra: skor | Sonra: sonuç |
|---|---|---|---|---|
| hava durumu nasıl olacak | 0.50 | ❌ *İmar durum belgesi nasıl alınır?* | 0.00 | ✅ |
| bugün günlerden ne | 0.47 | ❌ *Mahallemde çöpler hangi günler toplanıyor?* | 0.00 | ✅ |
| yarın hava yağışlı mı | 0.00 | ✅ | 0.00 | ✅ |
| futbol maçı kaç kaç bitti | 0.00 | ✅ | 0.00 | ✅ |
| pizza siparişi vermek istiyorum | 0.00 | ✅ | 0.00 | ✅ |
| dolar kuru ne kadar | 0.00 | ✅ | 0.00 | ✅ |
| en yakın eczane nerede | 0.00 | ✅ | 0.00 | ✅ |
| hastane randevusu almak istiyorum | 0.22 | ✅ | 0.18 | ✅ |
| ehliyet nasıl alınır | 0.23 | ✅ | 0.27 | ✅ |
| elektrik faturamı nasıl öderim | 0.32 | ✅ *(ama Su dairesine yönlendiriliyordu)* | 0.32 | ✅ *kapsam dışı → Beyaz Masa* |
| doğalgaz kesintisi ne zaman bitecek | 0.46 | ❌ *Mahallemde sular kesik, ne zaman gelecek?* | 0.29 | ✅ |
| okul kayıtları ne zaman başlıyor | 0.32 | ✅ | 0.42 | ✅ *kapsam dışı* |
| askerlik yoklaması nereden yapılır | 0.28 | ✅ | 0.28 | ✅ |
| bana bir fıkra anlat | 0.00 | ✅ | 0.00 | ✅ |
| asdfgh qwerty | 0.00 | ✅ | 0.00 | ✅ |

> *“okul kayıtları”* sorusunun skoru 0.42'ye çıktı, yani tek başına skorla yanlış eşleşecekti. Kapsam dışı kontrolü (*okul*) sayesinde reddedildi.

## 3. Kontrol seti (20) – ayarlamada kullanılmadı

Bu sorular listeler ayarlandıktan **sonra** eklendi ve sonuçlarına göre hiçbir ayar yapılmadı.

| Mesaj (beklenen) | Önce: skor | Önce: sonuç | Sonra: skor | Sonra: sonuç |
|---|---|---|---|---|
| su aboneliği iptal etmek istiyorum (Su ve Kanalizasyon) | 0.54 | ✅ | 0.54 | ✅ |
| imar planına nasıl bakarım (İmar ve Şehircilik) | 0.64 | ✅ | 0.64 | ✅ |
| iş yeri ruhsatı için hangi belgeler lazım (Zabıta) | 0.63 | ✅ | 0.63 | ✅ |
| geri dönüşüm kutusu nerede (Temizlik İşleri) | 0.51 | ✅ | 0.51 | ✅ |
| parktaki bank kırık (Park ve Bahçeler) | 0.60 | ✅ | 0.60 | ✅ |
| yabancı biriyle evlenmek istiyorum (Evlilik/Nikah) | 0.60 | ✅ | 0.60 | ✅ |
| tabela için reklam vergisi (Emlak/Vergi) | 0.73 | ✅ | 0.73 | ✅ |
| 65 yaş üstü ücretsiz kart (Ulaşım) | 0.77 | ✅ | 0.77 | ✅ |
| ihtiyaç sahiplerine yardım başvurusu (Kültür ve Sosyal İşler) | 0.53 | ✅ | 0.53 | ✅ |
| e-belediyeye nasıl kayıt olurum (Bilgi İşlem/BİMER) | 0.64 | ✅ | 0.64 | ✅ |
| telefon faturamı ödemek istiyorum (reddedilmeli) | 0.51 | ❌ *Su faturamı nasıl ödeyebilirim?* | 0.51 | ❌ *Su faturamı nasıl ödeyebilirim?* |
| kimlik kartımı yenilemek istiyorum (reddedilmeli) | 0.38 | ❌ *Öğrenci kartı nasıl çıkarılır?* | 0.38 | ❌ *Öğrenci kartı nasıl çıkarılır?* |
| nöbetçi eczane hangisi (reddedilmeli) | 0.00 | ✅ | 0.00 | ✅ |
| üniversite tercihleri ne zaman (reddedilmeli) | 0.47 | ❌ *Emlak vergisi ne zaman ödenir?* | 0.00 | ✅ |
| namaz vakitleri (reddedilmeli) | 0.00 | ✅ | 0.00 | ✅ |
| araba kiralamak istiyorum (reddedilmeli) | 0.42 | ❌ *Düğün salonu veya sosyal tesis kiralayabilir miyim?* | 0.42 | ❌ *Düğün salonu veya sosyal tesis kiralayabilir miyim?* |
| kira artış oranı ne kadar (reddedilmeli) | 0.00 | ✅ | 0.00 | ✅ |
| internet paketim bitti (reddedilmeli) | 0.39 | ❌ *Belediyenin ücretsiz Wi-Fi hizmeti nerelerde var?* | 0.39 | ❌ *Belediyenin ücretsiz Wi-Fi hizmeti nerelerde var?* |
| vergi dairesi nerede (reddedilmeli) | 0.42 | ❌ *Emlak vergisi ne zaman ödenir?* | 0.47 | ❌ *Emlak vergisi ne zaman ödenir?* |
| doğalgaz faturası çok yüksek geldi (reddedilmeli) | 0.73 | ❌ *Su faturam çok yüksek geldi…* | 0.73 | ✅ |

### Kalan hataların ortak nedeni

Kalan 5 hatanın hepsinde vatandaşın sorusu, bir belediye SSS'siyle **konuyu belirleyen kelimeyi** paylaşıyor: *fatura, kart, kiralamak, internet, vergi*. Farkı yaratan kelime (*telefon, kimlik, araba, paket, daire*) ise SSS sözlüğünde hiç yok ve TF-IDF tarafından yok sayılıyor.

Bunları tek tek kapsam dışı listesine eklemek bu 5 soruyu düzeltirdi. Ancak bu, test setine göre ayar yapmak (ezber) olurdu ve gerçek başarıyı yansıtmazdı. Kalıcı çözüm için anlamı dikkate alan bir yöntem gerekir; README'deki “Geliştirme fikirleri” bölümüne bakın.
