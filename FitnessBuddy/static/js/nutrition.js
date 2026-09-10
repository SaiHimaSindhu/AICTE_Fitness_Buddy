document.getElementById("btnGenerateMeal").addEventListener("click", async () => {
    const loading = document.getElementById("nutritionLoading");
    const resultBox = document.getElementById("nutritionResult");
    loading.classList.remove("d-none");
    resultBox.classList.add("d-none");

    try {
        const data = await fbFetch("/api/nutrition/plan", { method: "POST" });
        document.getElementById("calorieTarget").textContent = `${data.calorie_target} kcal`;
        document.getElementById("mealPlanText").textContent = data.plan;
        resultBox.classList.remove("d-none");
    } catch (err) {
        alert(err.message);
    } finally {
        loading.classList.add("d-none");
    }
});
