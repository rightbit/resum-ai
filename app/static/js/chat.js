// Handles the AI chat interface: submits questions via fetch (no full page
// reload) and appends the question/answer to the conversation thread.
(function () {
    const form = document.getElementById("chat-form");
    const input = document.getElementById("chat-input");
    const messages = document.getElementById("chat-messages");
    const errorBox = document.getElementById("chat-error");

    if (!form) {
        return;
    }

    function appendMessage(role, text) {
        const wrapper = document.createElement("div");
        wrapper.className = "chat-message chat-message-" + role;
        const bubble = document.createElement("div");
        bubble.className = "chat-bubble";
        bubble.textContent = text;
        wrapper.appendChild(bubble);
        messages.appendChild(wrapper);
        messages.scrollTop = messages.scrollHeight;
    }

    form.addEventListener("submit", async function (event) {
        event.preventDefault();
        errorBox.textContent = "";
        const question = input.value.trim();
        if (!question) {
            return;
        }

        appendMessage("user", question);
        input.value = "";
        input.disabled = true;

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: "question=" + encodeURIComponent(question),
            });
            const data = await response.json();
            if (!response.ok) {
                errorBox.textContent = data.error || "Something went wrong.";
            } else {
                appendMessage("assistant", data.answer);
            }
        } catch (err) {
            errorBox.textContent = "Network error. Please try again.";
        } finally {
            input.disabled = false;
            input.focus();
        }
    });
})();
