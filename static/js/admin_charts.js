/* =====================================================================
   Admin istatistik sayfası grafikleri (Chart.js - yerel dosya)
   Veriler sayfaya window.CHART_DATA olarak gömülür (bkz. istatistik.html).
   ===================================================================== */

(function () {
    "use strict";

    if (typeof Chart === "undefined" || !window.CHART_DATA) return;

    const data = window.CHART_DATA;
    const PRIMARY = "#0e5a5f";
    const ACCENT = "#c98a2e";
    const GRID = "#ece4d6";

    Chart.defaults.font.family = 'system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif';
    Chart.defaults.color = "#5f554b";

    // 1) En çok sorulan kategoriler: yatay çubuk grafik (uzun kategori adları okunaklı olsun)
    const categoryCanvas = document.getElementById("categoryChart");
    if (categoryCanvas) {
        new Chart(categoryCanvas, {
            type: "bar",
            data: {
                labels: data.categories.labels,
                datasets: [{
                    label: "Soru sayısı",
                    data: data.categories.values,
                    backgroundColor: PRIMARY,
                    borderRadius: 4,
                    maxBarThickness: 22,
                }],
            },
            options: {
                indexAxis: "y",
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: GRID } },
                    y: { grid: { display: false } },
                },
            },
        });
    }

    // 2) Cevaplanan / cevaplanamayan: halka grafik
    const answeredCanvas = document.getElementById("answeredChart");
    if (answeredCanvas) {
        new Chart(answeredCanvas, {
            type: "doughnut",
            data: {
                labels: data.answered.labels,
                datasets: [{
                    data: data.answered.values,
                    backgroundColor: [PRIMARY, ACCENT],
                    borderColor: "#ffffff",
                    borderWidth: 2,
                }],
            },
            options: {
                maintainAspectRatio: false,
                cutout: "62%",
                plugins: { legend: { position: "bottom" } },
            },
        });
    }

    // 3) Son 7 günün mesaj sayısı: çubuk grafik
    const dailyCanvas = document.getElementById("dailyChart");
    if (dailyCanvas) {
        new Chart(dailyCanvas, {
            type: "bar",
            data: {
                labels: data.daily.labels,
                datasets: [{
                    label: "Mesaj",
                    data: data.daily.values,
                    backgroundColor: ACCENT,
                    borderRadius: 4,
                    maxBarThickness: 36,
                }],
            },
            options: {
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: GRID } },
                    x: { grid: { display: false } },
                },
            },
        });
    }
})();
