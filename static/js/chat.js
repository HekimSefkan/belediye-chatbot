/* =====================================================================
   Sohbet widget'ı (vanilla JavaScript, harici kütüphane yok)

   Görevleri:
   - Sağ alttaki balona tıklanınca sohbet penceresini açıp kapatmak
   - Kullanıcının mesajını /api/chat adresine gönderip cevabı göstermek
   - Cevap bulunamazsa önerileri ve "talep oluştur" seçeneğini sunmak
   - Talep formunu gösterip /api/talep adresine göndermek

   GÜVENLİK: Mesajlar ekrana innerHTML ile değil textContent ile yazılır.
   Böylece kullanıcı "<script>" gibi bir metin yazsa bile kod olarak çalışmaz (XSS önlemi).
   ===================================================================== */

(function () {
    "use strict";

    // ---- Sayfadaki elemanlar ----
    const toggleBtn = document.getElementById("chat-toggle");
    const panel = document.getElementById("chat-panel");
    const closeBtn = document.getElementById("chat-close");
    const messagesEl = document.getElementById("chat-messages");
    const form = document.getElementById("chat-form");
    const input = document.getElementById("chat-input");
    const sendBtn = document.getElementById("chat-send");
    const quickBtn = document.getElementById("btn-quick");
    const ticketBtn = document.getElementById("btn-ticket");

    // ---- Durum değişkenleri ----
    let welcomed = false;      // Karşılama mesajı gösterildi mi?
    let busy = false;          // Sunucudan cevap bekleniyor mu?
    let quickData = null;      // /api/hizli-sorular önbelleği
    let departments = null;    // /api/departmanlar önbelleği
    let formCounter = 0;       // Her talep formuna benzersiz id vermek için

    // Sunucudaki sınırlarla aynı (routes/api_routes.py -> FIELD_LIMITS)
    const MAX_SUBJECT_LENGTH = 150;

    // =================================================================
    // Yardımcı fonksiyonlar
    // =================================================================

    /** Yeni bir HTML elemanı oluşturur; metni güvenli şekilde textContent ile ekler. */
    function el(tag, className, text) {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    }

    function scrollToBottom() {
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    /** JSON gönderip JSON cevap alan küçük fetch sarmalayıcısı. */
    async function postJSON(url, data) {
        const response = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        const body = await response.json().catch(function () { return {}; });
        return { ok: response.ok, body: body };
    }

    async function getJSON(url) {
        const response = await fetch(url);
        if (!response.ok) throw new Error("İstek başarısız: " + url);
        return response.json();
    }

    // =================================================================
    // Pencereyi açma / kapatma
    // =================================================================

    function openChat() {
        panel.hidden = false;
        toggleBtn.classList.add("is-open");
        toggleBtn.setAttribute("aria-expanded", "true");
        toggleBtn.setAttribute("aria-label", "Sohbet penceresini kapat");
        if (!welcomed) {
            welcomed = true;
            showWelcome();
        }
        input.focus();
    }

    function closeChat() {
        panel.hidden = true;
        toggleBtn.classList.remove("is-open");
        toggleBtn.setAttribute("aria-expanded", "false");
        toggleBtn.setAttribute("aria-label", "Sohbet penceresini aç");
        toggleBtn.focus();
    }

    // =================================================================
    // Mesaj baloncukları
    // =================================================================

    /** Sohbete bir mesaj ekler. sender: "user" veya "bot". Baloncuk elemanını döndürür. */
    function addMessage(sender, text) {
        const row = el("div", "msg msg--" + sender);
        const bubble = el("div", "msg__bubble", text);
        row.appendChild(bubble);
        messagesEl.appendChild(row);
        scrollToBottom();
        return bubble;
    }

    /** Baloncukların altına küçük gri açıklama satırı ekler. */
    function addNote(text) {
        const row = el("div", "msg msg--bot");
        row.appendChild(el("p", "msg__note", text));
        messagesEl.appendChild(row);
        scrollToBottom();
    }

    /**
     * Tıklanabilir buton grubu ekler.
     * items: [{ label, onClick, primary, once }]
     * once=true ise butonlardan birine tıklanınca grup devre dışı kalır (iki kez talep açılmasın).
     * row: (isteğe bağlı) önceden sohbete eklenmiş boş satır; verilmezse yenisi oluşturulur.
     */
    function addChips(items, row) {
        row = row || el("div", "msg msg--bot");
        const wrap = el("div", "chips");
        items.forEach(function (item) {
            const chip = el("button", "chip" + (item.primary ? " chip--primary" : ""), item.label);
            chip.type = "button";
            chip.addEventListener("click", function () {
                if (item.once) {
                    wrap.querySelectorAll("button").forEach(function (b) { b.disabled = true; });
                }
                item.onClick();
            });
            wrap.appendChild(chip);
        });
        row.appendChild(wrap);
        if (!row.parentNode) messagesEl.appendChild(row);
        scrollToBottom();
    }

    /** "Yazıyor..." göstergesini ekler; kaldırmak için dönen elemanın remove() metodu çağrılır. */
    function showTyping() {
        const row = el("div", "msg msg--bot");
        const bubble = el("div", "msg__bubble typing");
        // role="status": ekran okuyucu "Asistan yazıyor" metnini seslendirir
        bubble.setAttribute("role", "status");
        bubble.append(el("i"), el("i"), el("i"), el("span", "visually-hidden", "Asistan yazıyor…"));
        row.appendChild(bubble);
        messagesEl.appendChild(row);
        scrollToBottom();
        return row;
    }

    function setBusy(state) {
        busy = state;
        sendBtn.disabled = state;
    }

    // =================================================================
    // Karşılama ve hızlı sorular
    // =================================================================

    function showWelcome() {
        addMessage(
            "bot",
            "Merhaba! 👋 Ben Mardin Büyükşehir Belediyesi vatandaş hizmetleri asistanıyım.\n" +
            "Sorunuzu yazabilir veya aşağıdan bir konu seçebilirsiniz."
        );
        showCategories();
    }

    async function loadQuickData() {
        if (quickData === null) {
            quickData = await getJSON("/api/hizli-sorular");
        }
        return quickData;
    }

    /** Kategori butonlarını gösterir. */
    async function showCategories() {
        // Satırı hemen ekliyoruz; veri sunucudan gelene kadar kullanıcı mesaj gönderse bile
        // butonlar yine doğru sırada (karşılama mesajının altında) görünür.
        const row = el("div", "msg msg--bot");
        messagesEl.appendChild(row);
        try {
            const groups = await loadQuickData();
            addChips(groups.map(function (group) {
                return {
                    label: group.kategori,
                    onClick: function () { showQuestionsOf(group); },
                };
            }), row);
        } catch (error) {
            row.appendChild(el("p", "msg__note", "Hızlı sorular şu anda yüklenemedi, sorunuzu yazarak sorabilirsiniz."));
        }
    }

    /** Seçilen kategorinin sorularını buton olarak gösterir. */
    function showQuestionsOf(group) {
        addNote(group.kategori + " ile ilgili sık sorulan sorular:");
        addChips(group.sorular.map(function (question) {
            return { label: question, onClick: function () { sendMessage(question); } };
        }));
    }

    // =================================================================
    // Mesaj gönderme ve cevabı gösterme
    // =================================================================

    async function sendMessage(text) {
        text = (text || "").trim();
        if (!text || busy) return;

        openChat();
        addMessage("user", text);
        input.value = "";
        setBusy(true);
        const typing = showTyping();

        try {
            const result = await postJSON("/api/chat", { message: text });
            typing.remove();
            if (!result.ok) {
                addMessage("bot", result.body.error || "Bir hata oluştu, lütfen tekrar deneyin.");
                return;
            }
            renderBotReply(result.body, text);
        } catch (error) {
            typing.remove();
            addMessage("bot", "Sunucuya ulaşılamadı. Lütfen bağlantınızı kontrol edip tekrar deneyin.");
        } finally {
            setBusy(false);
            input.focus();
        }
    }

    /** /api/chat cevabını türüne göre ekrana yazar. */
    function renderBotReply(data, userText) {
        const bubble = addMessage("bot", data.answer);

        // Selamlama cevabı "aşağıdaki konulardan birini seçin" dediği için konuları göster
        if (data.type === "greeting") {
            showCategories();
            return;
        }

        // Cevap bulunduysa hangi kategori ve birimden geldiğini göster
        if (data.type === "answer") {
            bubble.appendChild(el(
                "span",
                "msg__meta",
                data.category + " · İlgili birim: " + data.department
            ));
            return;
        }

        // Cevap bulunamadıysa veya konu kapsam dışıysa: öneriler + talep oluşturma teklifi
        if (data.offer_ticket) {
            if (data.suggestions && data.suggestions.length) {
                addNote("Şunlardan birini mi sormak istediniz?");
                addChips(data.suggestions.map(function (question) {
                    return { label: question, onClick: function () { sendMessage(question); } };
                }));
            }
            addChips([
                {
                    label: "Evet, talep oluştur",
                    primary: true,
                    once: true,
                    onClick: function () {
                        showTicketForm({ konu: userText, departman: data.department });
                    },
                },
                {
                    label: "Hayır, teşekkürler",
                    once: true,
                    onClick: function () {
                        addMessage("bot", "Anlaşıldı. Başka bir sorunuz olursa buradayım.");
                    },
                },
            ]);
        }
    }

    // =================================================================
    // Talep / şikayet formu
    // =================================================================

    async function loadDepartments() {
        if (departments === null) {
            departments = await getJSON("/api/departmanlar");
        }
        return departments;
    }

    /** Form alanı oluşturur: etiket + giriş elemanı + hata mesajı yeri. */
    function createField(options) {
        const label = el("label");
        label.htmlFor = options.id;
        label.dataset.field = options.name;

        const title = el("span", null, options.label);
        if (options.optional) title.appendChild(el("span", "optional", " (isteğe bağlı)"));
        label.appendChild(title);

        const control = document.createElement(options.tag || "input");
        control.id = options.id;
        control.name = options.name;
        if (options.type) control.type = options.type;
        if (options.maxLength) control.maxLength = options.maxLength;
        if (options.placeholder) control.placeholder = options.placeholder;
        if (options.value) control.value = options.value;
        label.appendChild(control);

        // Hata mesajı alana aria-describedby ile bağlanır; ekran okuyucu alanla birlikte okur
        const error = el("span", "field-error");
        error.id = options.id + "-hata";
        control.setAttribute("aria-describedby", error.id);
        label.appendChild(error);
        return { label: label, control: control, error: error };
    }

    /** Alanın hata durumunu ayarlar (message boşsa hatayı temizler). */
    function setFieldError(field, message) {
        field.label.classList.toggle("has-error", Boolean(message));
        field.error.textContent = message || "";
        if (message) {
            field.control.setAttribute("aria-invalid", "true");
        } else {
            field.control.removeAttribute("aria-invalid");
        }
    }

    async function showTicketForm(prefill) {
        prefill = prefill || {};
        openChat();

        // Açık bir form zaten varsa yenisini açma, ona odaklan
        const existing = messagesEl.querySelector(".ticket-form");
        if (existing) {
            existing.querySelector("input").focus();
            existing.scrollIntoView({ block: "nearest" });
            return;
        }

        let departmentList;
        try {
            departmentList = await loadDepartments();
        } catch (error) {
            addMessage("bot", "Talep formu şu anda açılamadı. Lütfen daha sonra tekrar deneyin.");
            return;
        }

        formCounter += 1;
        const prefix = "tf" + formCounter + "-";

        // Vatandaşın sorusu konu alanına sığmıyorsa (en fazla 150 karakter) kısaltılır,
        // sorunun tamamı açıklama alanına yazılır. Böylece "en fazla 150 karakter" hatası çıkmaz.
        let subject = prefill.konu || "";
        let description = "";
        if (subject.length > MAX_SUBJECT_LENGTH) {
            description = subject;
            subject = subject.slice(0, MAX_SUBJECT_LENGTH - 1).trimEnd() + "…";
        }

        const row = el("div", "msg msg--bot msg--form");
        const ticketForm = el("form", "ticket-form");
        ticketForm.noValidate = true;
        ticketForm.appendChild(el("h4", null, "Talep / Şikayet Formu"));

        const fields = {
            ad_soyad: createField({ id: prefix + "ad", name: "ad_soyad", label: "Ad Soyad", maxLength: 100 }),
            telefon: createField({
                id: prefix + "tel", name: "telefon", label: "Telefon", type: "tel",
                optional: true, maxLength: 20, placeholder: "05xx xxx xx xx",
            }),
            departman: createField({ id: prefix + "dep", name: "departman", label: "İlgili Birim", tag: "select" }),
            konu: createField({
                id: prefix + "konu", name: "konu", label: "Konu", maxLength: MAX_SUBJECT_LENGTH, value: subject,
            }),
            aciklama: createField({
                id: prefix + "acik", name: "aciklama", label: "Açıklama", tag: "textarea", maxLength: 2000,
                placeholder: "Adres ve ayrıntıları yazmanız talebinizin hızlı çözülmesini sağlar.",
                value: description,
            }),
        };

        // Departman seçeneklerini doldur; chatbotun önerdiği birim seçili gelsin
        departmentList.forEach(function (name) {
            const option = el("option", null, name);
            option.value = name;
            if (name === prefill.departman) option.selected = true;
            fields.departman.control.appendChild(option);
        });

        Object.keys(fields).forEach(function (key) {
            ticketForm.appendChild(fields[key].label);
        });

        // Alanlara bağlı olmayan hatalar (sunucu/bağlantı hatası) için mesaj alanı
        const formError = el("p", "field-error form-error");
        formError.setAttribute("role", "alert");
        ticketForm.appendChild(formError);

        const actions = el("div", "form-actions");
        const submitBtn = el("button", "btn btn-primary", "Gönder");
        submitBtn.type = "submit";
        const cancelBtn = el("button", "btn btn-ghost", "Vazgeç");
        cancelBtn.type = "button";
        actions.append(submitBtn, cancelBtn);
        ticketForm.appendChild(actions);

        cancelBtn.addEventListener("click", function () {
            row.remove();
            addMessage("bot", "Talep formu kapatıldı. Başka bir konuda yardımcı olabilir miyim?");
        });

        ticketForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            // Önceki hata mesajlarını temizle
            Object.keys(fields).forEach(function (key) { setFieldError(fields[key], ""); });
            formError.textContent = "";

            const payload = {};
            Object.keys(fields).forEach(function (key) {
                payload[key] = fields[key].control.value.trim();
            });

            submitBtn.disabled = true;
            submitBtn.textContent = "Gönderiliyor…";

            try {
                const result = await postJSON("/api/talep", payload);
                if (result.ok) {
                    row.remove();
                    addMessage("bot", "✅ " + result.body.message);
                    return;
                }
                // Sunucudan gelen alan bazlı hataları ilgili alanın altında göster
                const errors = result.body.errors || {};
                const fieldKeys = Object.keys(errors).filter(function (key) { return fields[key]; });
                fieldKeys.forEach(function (key) { setFieldError(fields[key], errors[key]); });

                if (fieldKeys.length) {
                    fields[fieldKeys[0]].control.focus();
                } else {
                    // Alan hatası yoksa (ör. sunucu hatası) formun altında genel bir mesaj göster
                    formError.textContent = result.body.error ||
                        "Talebiniz şu anda kaydedilemedi. Lütfen biraz sonra tekrar deneyin.";
                }
            } catch (error) {
                formError.textContent = "Talep gönderilemedi. Lütfen bağlantınızı kontrol edip tekrar deneyin.";
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = "Gönder";
            }
        });

        row.appendChild(ticketForm);
        messagesEl.appendChild(row);
        scrollToBottom();
        fields.ad_soyad.control.focus();
    }

    // =================================================================
    // Olay dinleyicileri
    // =================================================================

    toggleBtn.addEventListener("click", function () {
        if (panel.hidden) openChat(); else closeChat();
    });
    closeBtn.addEventListener("click", closeChat);

    form.addEventListener("submit", function (event) {
        event.preventDefault();
        sendMessage(input.value);
    });

    quickBtn.addEventListener("click", function () {
        addNote("Bir konu seçin:");
        showCategories();
    });
    ticketBtn.addEventListener("click", function () { showTicketForm({}); });

    // Escape tuşu pencereyi kapatır
    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && !panel.hidden) closeChat();
    });

    // Sayfadaki "Hızlı Sorular" butonları ve diğer açma butonları
    document.querySelectorAll("[data-question]").forEach(function (button) {
        button.addEventListener("click", function () { sendMessage(button.dataset.question); });
    });
    document.querySelectorAll("[data-open-chat]").forEach(function (button) {
        button.addEventListener("click", openChat);
    });
    document.querySelectorAll("[data-open-ticket]").forEach(function (button) {
        button.addEventListener("click", function () { showTicketForm({}); });
    });
})();
