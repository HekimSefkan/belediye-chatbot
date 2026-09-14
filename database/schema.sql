-- ============================================================
-- Mardin Büyükşehir Belediyesi Vatandaş Hizmetleri Chatbotu
-- SQLite veritabanı şeması
-- "IF NOT EXISTS" sayesinde uygulama her açıldığında güvenle çalıştırılabilir.
-- ============================================================

-- Sık Sorulan Sorular: chatbotun cevap verdiği bilgi tabanı
CREATE TABLE IF NOT EXISTS faq (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    kategori          TEXT NOT NULL,                 -- örn. "Su ve Kanalizasyon"
    soru              TEXT NOT NULL,                 -- örnek vatandaş sorusu
    cevap             TEXT NOT NULL,                 -- botun vereceği cevap
    anahtar_kelimeler TEXT DEFAULT '',               -- eşleştirmeye yardımcı ek kelimeler (virgülle)
    departman         TEXT NOT NULL,                 -- sorudan sorumlu birim
    olusturma_tarihi  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- Vatandaşların chatbot üzerinden oluşturduğu talep ve şikayetler
CREATE TABLE IF NOT EXISTS talep_sikayet (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_soyad         TEXT NOT NULL,
    telefon          TEXT DEFAULT '',                -- opsiyonel
    konu             TEXT NOT NULL,
    aciklama         TEXT NOT NULL,
    departman        TEXT NOT NULL,
    durum            TEXT NOT NULL DEFAULT 'Beklemede'
                     CHECK (durum IN ('Beklemede', 'İşlemde', 'Tamamlandı')),
    olusturma_tarihi TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- Tüm sohbet geçmişi (istatistik ve SSS'yi geliştirmek için)
CREATE TABLE IF NOT EXISTS chat_log (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    kullanici_mesaji TEXT NOT NULL,
    bot_cevabi       TEXT NOT NULL,
    benzerlik_skoru  REAL NOT NULL DEFAULT 0,
    cevap_bulundu_mu INTEGER NOT NULL DEFAULT 0,     -- 1: cevap bulundu, 0: bulunamadı
    kategori         TEXT DEFAULT NULL,              -- eşleşen SSS'nin kategorisi (istatistik grafiği için)
    tarih            TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- Admin paneli kullanıcıları (şifre düz metin değil, hash olarak saklanır)
CREATE TABLE IF NOT EXISTS admin (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    kullanici_adi TEXT NOT NULL UNIQUE,
    sifre_hash   TEXT NOT NULL
);
