// Handles the AI chat interface: submits questions via fetch (no full page
// reload) and appends the question/answer to the conversation thread.
(function () {
    const form = document.getElementById("chat-form");
    const input = document.getElementById("chat-input");
    const messages = document.getElementById("chat-messages");
    const errorBox = document.getElementById("chat-error");
    const status = document.getElementById("chat-status");
    const statusDots = document.getElementById("chat-status-dots");
    const submitButton = form ? form.querySelector("button[type='submit']") : null;

    if (!form) {
        return;
    }

    let pendingTimer = null;
    let dotIndex = 0;
    const ellipsisStates = [".", "..", "..."];

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

    function startPendingIndicator() {
        if (!status || !statusDots) {
            return;
        }

        status.hidden = false;
        dotIndex = 0;
        statusDots.textContent = ellipsisStates[dotIndex];
        pendingTimer = window.setInterval(function () {
            dotIndex = (dotIndex + 1) % ellipsisStates.length;
            statusDots.textContent = ellipsisStates[dotIndex];
        }, 400);
    }

    function stopPendingIndicator() {
        if (pendingTimer) {
            window.clearInterval(pendingTimer);
            pendingTimer = null;
        }
        if (status) {
            status.hidden = true;
        }
        if (statusDots) {
            statusDots.textContent = ".";
        }
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
        if (submitButton) {
            submitButton.disabled = true;
        }
        startPendingIndicator();

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
            if (submitButton) {
                submitButton.disabled = false;
            }
            stopPendingIndicator();
            input.focus();
        }
    });
})();
