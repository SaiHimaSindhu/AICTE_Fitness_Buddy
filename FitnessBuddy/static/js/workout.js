const loadingEl = document.getElementById("workoutLoading");
const resultCard = document.getElementById("workoutResultCard");
const resultTitle = document.getElementById("workoutResultTitle");
const resultText = document.getElementById("workoutResultText");

function setLoading(isLoading) {
    loadingEl.classList.toggle("d-none", !isLoading);
    if (isLoading) resultCard.classList.add("d-none");
}

function showResult(title, text) {
    resultTitle.textContent = title;
    resultText.textContent = text;
    resultCard.classList.remove("d-none");
}

document.getElementById("btnFullPlan").addEventListener("click", async () => {
    setLoading(true);
    try {
        const data = await fbFetch("/api/workout/plan", { method: "POST" });
        showResult("Your 7-Day Workout Plan", data.plan);
    } catch (err) {
        showResult("Error", err.message);
    } finally {
        setLoading(false);
    }
});

document.getElementById("btnHomeWorkout").addEventListener("click", async () => {
    setLoading(true);
    try {
        const data = await fbFetch("/api/workout/home", { method: "POST" });
        showResult("Quick Home Workout", data.workout);
    } catch (err) {
        showResult("Error", err.message);
    } finally {
        setLoading(false);
    }
});

document.getElementById("btnTip").addEventListener("click", async () => {
    setLoading(true);
    try {
        const data = await fbFetch("/api/workout/tip");
        showResult("Fitness Tip", data.tip);
    } catch (err) {
        showResult("Error", err.message);
    } finally {
        setLoading(false);
    }
});
