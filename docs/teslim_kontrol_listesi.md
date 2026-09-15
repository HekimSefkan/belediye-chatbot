# Teslim Kontrol Listesi

> Bu proje bir staj çalışmasıdır. İçerdiği tüm veriler kurgusal demo verisidir, kurumun resmi verisi değildir.

Teslimden önce maddeleri sırayla uygula ve kutuları işaretle (`[ ]` → `[x]`).

## Uygulama

- [ ] **1. Temiz başlangıç:** Açık `basla.bat` penceresini kapat → `sifirla.bat` → `E` + Enter → *“Veritabanı yeniden oluşturuldu”* mesajı görünüyor.
- [ ] **2. Uygulama açılıyor:** `basla.bat` → konsolda `Sunucu: waitress` yazıyor, tarayıcı http://127.0.0.1:5000 adresinde açılıyor, sekmede sohbet balonu simgesi var.
- [ ] **3. Konsol temiz:** Sayfalar açılınca konsolda `404` veya *development server* uyarısı yok.
- [ ] **4. Testler geçiyor:** `testleri_calistir.bat` → *“122 passed”* ve *“TÜM TESTLER BAŞARIYLA GEÇTİ.”*
- [ ] **5. Admin girişi çalışıyor:** http://127.0.0.1:5000/admin → `admin` / `admin123` → İstatistikler sayfası ve grafikler açılıyor (varsayılan şifre uyarısı normaldir).

## Demo provası ([sunum taslağı](sunum_taslagi.md), Slayt 8)

- [ ] **6. Sohbet:** `çöpler hangi gün toplanıyor` → cevap ve ilgili birim; `faturami nerden oderim` → su faturası cevabı.
- [ ] **7. Kapsam dışı ve cevapsız soru:** `elektrik faturamı nasıl öderim` → *“hizmet alanı dışında”*; `sokak lambası yanmıyor` → Beyaz Masa + **Evet, talep oluştur**.
- [ ] **8. Talep formu:** Açıklamayı boş bırakıp **Gönder** → kırmızı hata ve özet görünüyor; doldurup gönder → talep numarası. Formun altında aydınlatma notu var.
- [ ] **9. Admin akışı:** Talepler → durumu *İşlemde* seç → **Kaydet**; İstatistikler → *sokak lambası yanmıyor* → **SSS olarak ekle** → kaydet → sohbette aynı soru artık cevaplanıyor.
- [ ] **10. Demo sonrası:** Uygulamayı kapat, `sifirla.bat` ile demo verisini temizle (sunumda tekrar göstereceksen).

## GitHub ve teslim dosyaları

- [ ] **11. GitHub güncel:** Proje klasöründe `git status` → *“nothing to commit, working tree clean”* ve *“up to date with 'origin/main'”*; https://github.com/HekimSefkan/belediye-chatbot sayfası açılıyor ve README'deki ekran görüntüleri görünüyor.
- [ ] **12. Rapor:** [staj_raporu_taslagi.md](staj_raporu_taslagi.md) içindeki `[köşeli parantezli]` yerler (kurum adı, tarihler, gözlemler, kazanımlar) dolduruldu; ekran görüntüleri [ekran_goruntuleri/](ekran_goruntuleri/) klasöründen eklendi.
- [ ] **13. Sunum:** [sunum_taslagi.md](sunum_taslagi.md)'ye göre slaytlar hazır; yedek slayttaki ekran görüntüleri eklendi; [savunma_sorulari.md](savunma_sorulari.md) okundu.
- [ ] **14. Teslim edilecekler:** (1) Staj raporu, (2) sunum dosyası, (3) GitHub bağlantısı. Kaynak kod ZIP olarak istenirse GitHub'da **Code → Download ZIP** (içinde `venv`, `.env`, veritabanı ve `instance/` klasörü **olmamalı**).
- [ ] **15. Son bakış:** Sunumu yapacağın bilgisayarda madde 1–5'i bir kez daha uygula (internet bağlantısı gerekmez).
