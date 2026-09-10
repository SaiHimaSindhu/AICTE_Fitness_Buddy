const chatWindow = document.getElementById("chatWindow");
const chatInput = document.getElementById("chatInput");
const chatSendBtn = document.getElementById("chatSendBtn");

function appendBubble(text, sender) {
    const div = document.createElement("div");
    div.className = `fb-chat-bubble ${sender === "user" ? "fb-chat-user" : "fb-chat-bot"}`;
    div.textContent = text;
    chatWindow.appendChild(div);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

async function sendMessage(question) {
    if (!question.trim()) return;
    appendBubble(question, "user");
    chatInput.value = "";
    appendBubble("Typing...", "bot");
    const typingBubble = chatWindow.lastChild;

    try {
        const data = await fbFetch("/api/chat", {
            method: "POST",
            body: JSON.stringify({ question }),
        });
        typingBubble.textContent = data.response;
    } catch (err) {
        typingBubble.textContent = "Sorry, I couldn't process that. Please try again.";
    }
}

chatSendBtn.addEventListener("click", () => sendMessage(chatInput.value));
chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage(chatInput.value);
});

document.querySelectorAll(".fb-suggestion").forEach((btn) => {
    btn.addEventListener("click", () => sendMessage(btn.textContent));
});

chatWindow.scrollTop = chatWindow.scrollHeight;
