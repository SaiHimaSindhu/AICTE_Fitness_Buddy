document.getElementById("registerForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.target;
    const btn = document.getElementById("registerBtn");
    const alertBox = document.getElementById("registerAlert");
    alertBox.classList.add("d-none");

    const payload = Object.fromEntries(new FormData(form).entries());

    btn.disabled = true;
    btn.textContent = "Creating your profile...";

    try {
        const data = await fbFetch("/api/register", {
            method: "POST",
            body: JSON.stringify(payload),
        });
        window.location.href = data.redirect || "/dashboard";
    } catch (err) {
        fbShowAlert(alertBox, err.message);
        btn.disabled = false;
        btn.textContent = "Create Profile & Start";
    }
});
