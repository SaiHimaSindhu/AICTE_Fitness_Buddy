(async () => {
    const quoteEl = document.getElementById("motivationQuote");
    const habitEl = document.getElementById("habitTip");
    try {
        const data = await fbFetch("/api/motivation");
        quoteEl.textContent = `"${data.quote}"`;
        habitEl.innerHTML = `<i class="bi bi-lightbulb"></i> <strong>Habit tip:</strong> ${data.habit_tip}`;
    } catch (err) {
        quoteEl.textContent = "Stay consistent — you're doing great!";
        habitEl.textContent = "";
    }
})();
