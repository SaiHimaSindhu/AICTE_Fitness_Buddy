/* Fitness Buddy — shared frontend helpers */

async function fbFetch(url, options = {}) {
    const opts = Object.assign(
        { headers: { "Content-Type": "application/json" } },
        options
    );
    const res = await fetch(url, opts);
    let data;
    try {
        data = await res.json();
    } catch (e) {
        data = { success: false, error: "Unexpected server response." };
    }
    if (!res.ok || data.success === false) {
        throw new Error(data.error || `Request failed (${res.status})`);
    }
    return data;
}

function fbShowAlert(el, message, type = "danger") {
    if (!el) return;
    el.className = `alert alert-${type}`;
    el.textContent = message;
    el.classList.remove("d-none");
}
