let weightChart, waterChart;

async function loadProgress() {
    const data = await fbFetch(`/api/progress/${window.FB_USER_ID}`);
    const rows = data.progress;
    const labels = rows.map(r => r.date);
    const weights = rows.map(r => r.weight);
    const waters = rows.map(r => r.water_intake);

    const ctxW = document.getElementById("weightChart");
    const ctxWater = document.getElementById("waterChart");

    if (weightChart) weightChart.destroy();
    if (waterChart) waterChart.destroy();

    weightChart = new Chart(ctxW, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label: "Weight (kg)",
                data: weights,
                borderColor: "#2E7D32",
                backgroundColor: "rgba(46,125,50,0.1)",
                tension: 0.3,
                fill: true,
            }],
        },
        options: { responsive: true, plugins: { legend: { display: false } } },
    });

    waterChart = new Chart(ctxWater, {
        type: "bar",
        data: {
            labels,
            datasets: [{
                label: "Water Intake (L)",
                data: waters,
                backgroundColor: "#FF7043",
            }],
        },
        options: { responsive: true, plugins: { legend: { display: false } } },
    });

    const s = data.summary;
    document.getElementById("weeklySummaryList").innerHTML = `
        <li><i class="bi bi-check2-circle text-success"></i> Workouts completed: <strong>${s.workouts_completed}/7</strong></li>
        <li><i class="bi bi-droplet text-primary"></i> Avg water intake: <strong>${s.avg_water} L</strong></li>
        <li><i class="bi bi-arrow-down-up"></i> Weight change: <strong>${s.weight_change} kg</strong></li>
        <li><i class="bi bi-calendar-check"></i> Days logged: <strong>${s.days_logged}</strong></li>
    `;
}

document.getElementById("progressForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.target;
    const alertBox = document.getElementById("progressAlert");
    const payload = {
        weight: form.weight.value || null,
        water_intake: form.water_intake.value || null,
        workout_done: form.workout_done.checked,
    };
    try {
        await fbFetch("/api/progress", { method: "POST", body: JSON.stringify(payload) });
        fbShowAlert(alertBox, "Today's progress saved!", "success");
        await loadProgress();
    } catch (err) {
        fbShowAlert(alertBox, err.message, "danger");
    }
});

loadProgress();
