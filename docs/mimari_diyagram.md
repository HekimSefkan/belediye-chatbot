# Mimari Diyagram

> Bu proje bir staj çalışmasıdır. İçerdiği tüm veriler kurgusal demo verisidir, kurumun resmi verisi değildir.

Uygulama klasik **üç katmanlı** bir web uygulamasıdır: tarayıcıdaki arayüz, Flask sunucusu ve SQLite veritabanı. Doğal dil eşleştirmesi, sunucunun içinde çalışan bir Python modülüdür. Dışarıdaki hiçbir servise istek gönderilmez.

## 1. Genel yapı

```mermaid
flowchart LR
    subgraph Tarayici["Tarayıcı"]
        V["Vatandaş arayüzü<br/>index.html + chat.js"]
        A["Admin paneli<br/>admin/*.html + Chart.js"]
    end

    subgraph Sunucu["Flask sunucusu (app.py)"]
        CR["chat_routes<br/>GET /"]
        API["api_routes<br/>/api/chat, /api/talep ..."]
        AR["admin_routes<br/>/admin/..."]
        subgraph Bot["chatbot paketi"]
            P["preprocessor<br/>metin temizleme"]
            M["matcher<br/>TF-IDF + cosine"]
            R["responses<br/>cevap üretimi"]
        end
    end

    DB[("SQLite<br/>chatbot.db")]

    V -- "sayfa isteği" --> CR
    V -- "fetch (JSON)" --> API
    A -- "form / sayfa" --> AR
    API --> R --> M --> P
    CR --> DB
    API --> DB
    AR --> DB
    AR -- "SSS değişince yeniden eğit" --> M
```

## 2. Bir mesajın yolculuğu (`POST /api/chat`)

```mermaid
sequenceDiagram
    actor Vatandas as Vatandaş
    participant JS as chat.js
    participant API as api_routes.chat()
    participant RESP as responses.build_response()
    participant MATCH as FAQMatcher
    participant DB as SQLite

    Vatandas->>JS: "cop toplama gunleri" yazar
    JS->>API: POST /api/chat {message}
    API->>API: Boş mu? 500 karakterden uzun mu?
    API->>RESP: build_response(message)
    RESP->>RESP: Selamlama / teşekkür mü?
    RESP->>MATCH: find_best_match(message)
    MATCH->>MATCH: clean_text → "cop topla" ("gunleri" stopword)
    MATCH->>MATCH: TF-IDF vektörü + cosine similarity
    MATCH->>MATCH: Kapsam dışı kelime kontrolü
    MATCH-->>RESP: {faq, score: 0.70, found: true, out_of_scope: false}
    RESP-->>API: cevap, kategori, departman
    API->>DB: INSERT INTO chat_log (...)
    API-->>JS: JSON cevap
    JS-->>Vatandas: Cevap baloncuğu + "İlgili birim"
```

## 3. Karar mantığı

```mermaid
flowchart TD
    S["Mesaj geldi"] --> G{"Selamlama veya<br/>teşekkür mü?"}
    G -- Evet --> GR["Hazır kısa cevap"]
    G -- Hayır --> T["TF-IDF ile en benzer SSS'yi bul"]
    T --> K{"Kapsam dışı kelime var mı?<br/>(elektrik, doğalgaz, hastane...)<br/>ve SSS'de geçmiyor mu?"}
    K -- Evet --> KD["'Hizmet alanımız dışında'<br/>+ Beyaz Masa"]
    K -- Hayır --> C{"skor ≥ 0.35 ?"}
    C -- Evet --> OK["SSS cevabı + departman"]
    C -- Hayır --> Y{"skor ≥ 0.30 ?"}
    Y -- Evet --> D1["En yakın SSS'nin departmanına yönlendir"]
    Y -- Hayır --> D2["Beyaz Masa'ya yönlendir"]
    D1 --> O["Benzer soru önerileri +<br/>'Talep olarak kaydedeyim mi?'"]
    D2 --> O
    KD --> O2["'Talep olarak kaydedeyim mi?'"]
    O --> F["Evet → sohbet içinde talep formu → POST /api/talep"]
    O2 --> F
```

**Kapsam dışı kontrolü neden var?** TF-IDF kelime benzerliğine baktığı için *“doğalgaz faturası çok yüksek geldi”* sorusu, *“Su faturam çok yüksek geldi”* SSS'siyle 0.73 skor alır. Belediyenin görev alanı dışındaki konuları gösteren küçük bir kelime listesi (`chatbot/preprocessor.py` → `OUT_OF_SCOPE_WORDS`) bu tür yanlış cevapları engeller.

## 4. Katmanların görevleri

| Katman | Dosyalar | Görev |
|---|---|---|
| Sunum (arayüz) | `templates/`, `static/` | Sohbet penceresi, hızlı sorular, admin ekranları |
| Uygulama (Flask) | `app.py`, `routes/` | İstekleri karşılama, doğrulama, oturum, yönlendirme |
| İş mantığı | `chatbot/` | Metin ön işleme, eşleştirme, cevap üretimi |
| Veri | `database/` | Tablo şeması, demo veri, sorgu yardımcıları |

## 5. Tasarım kararları

- **Application factory (`create_app`)**: Testlerde geçici veritabanıyla ayrı bir uygulama örneği oluşturabilmek için kullanılır.
- **Blueprint'ler**: Vatandaş sayfası, API ve admin paneli ayrı dosyalarda tutulur. Böylece kod okunabilir kalır.
- **Model bellekte**: TF-IDF modeli her mesajda değil, uygulama açılırken bir kez eğitilir. SSS eklenince veya değişince yeniden eğitilir, bu yüzden cevaplar milisaniyeler içinde döner.
- **Ücretli API yok**: Belediye ağında internet kısıtlı olabileceği için tüm bileşenler (Chart.js dahil) yereldedir.
- **Sunucu: waitress**: `app.py` uygulamayı Flask'ın geliştirme sunucusu yerine saf Python bir üretim (WSGI) sunucusu olan waitress ile `127.0.0.1` üzerinde başlatır. Sadece `FLASK_DEBUG=True` iken geliştirme sunucusu kullanılır.
