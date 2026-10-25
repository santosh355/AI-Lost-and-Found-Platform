const API_URL = "http://127.0.0.1:5000/api";

let currentUser = null;
let currentAuthMode = "register";
let activeChatSession = null;
let chatPollInterval = null;

function toggleAuthIdField() {
    const role = document.getElementById("auth_role").value;
    const idGroup = document.getElementById("studentIdGroup");
    const idInput = document.getElementById("auth_id");

    if (role === "Faculty") {
        idGroup.style.display = "none";
        idInput.required = false;
        idInput.value = "";
    } else {
        idGroup.style.display = "block";
        idInput.required = true;
    }
}

function switchAuthMode(mode) {
    currentAuthMode = mode;

    const title = document.querySelector("#authModal h2");
    const submitBtn = document.getElementById("authSubmitBtn");
    const fullNameGroup = document.getElementById("fullNameGroup");
    const roleGroup = document.getElementById("roleGroup");
    const studentIdGroup = document.getElementById("studentIdGroup");
    const passwordGroup = document.getElementById("passwordGroup");
    const newPasswordGroup = document.getElementById("newPasswordGroup");
    const forgotLink = document.getElementById("forgotPasswordLinkContainer");

    const tabReg = document.getElementById("tabRegister");
    const tabLog = document.getElementById("tabLogin");

    const nameInput = document.getElementById("auth_name");
    const passInput = document.getElementById("auth_password");
    const newPassInput = document.getElementById("auth_new_password");

    // Reset active tabs
    tabReg.classList.remove("active");
    tabLog.classList.remove("active");

    if (mode === "login") {
        title.innerText = "Login to Portal";
        submitBtn.innerText = "Login";
        fullNameGroup.style.display = "none";
        roleGroup.style.display = "none";
        studentIdGroup.style.display = "none";
        passwordGroup.style.display = "block";
        newPasswordGroup.style.display = "none";
        forgotLink.style.display = "block"; // Show "Forgot password?" link below login button

        nameInput.required = false;
        passInput.required = true;
        newPassInput.required = false;
        tabLog.classList.add("active");
    } else if (mode === "forgot") {
        title.innerText = "Reset Password";
        submitBtn.innerText = "Update Password";
        fullNameGroup.style.display = "none";
        roleGroup.style.display = "none";
        studentIdGroup.style.display = "none";
        passwordGroup.style.display = "none";
        newPasswordGroup.style.display = "block";
        forgotLink.style.display = "none";

        nameInput.required = false;
        passInput.required = false;
        newPassInput.required = true;
    } else {
        title.innerText = "Register Account";
        submitBtn.innerText = "Register";
        fullNameGroup.style.display = "block";
        roleGroup.style.display = "block";
        studentIdGroup.style.display = "block";
        passwordGroup.style.display = "block";
        newPasswordGroup.style.display = "none";
        forgotLink.style.display = "none";

        nameInput.required = true;
        passInput.required = true;
        newPassInput.required = false;
        tabReg.classList.add("active");
    }
}

function toggleUserDropdown(event) {
    event.stopPropagation();
    document.getElementById("userDropdownMenu").classList.toggle("show");
}

window.addEventListener("click", () => {
    const menu = document.getElementById("userDropdownMenu");

    if (menu && menu.classList.contains("show")) {
        menu.classList.remove("show");
    }
});

async function handleAuthSubmit(event) {
    event.preventDefault();

    try {
        const email = document.getElementById("auth_email").value.trim();

        if (currentAuthMode === "register") {
            const full_name = document.getElementById("auth_name").value.trim();
            const role = document.getElementById("auth_role").value;
            const student_id =
                role === "Student"
                    ? document.getElementById("auth_id").value.trim()
                    : "Faculty_Staff";
            const password = document.getElementById("auth_password").value;

            const res = await fetch(`${API_URL}/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    full_name,
                    role,
                    student_id,
                    email,
                    password
                })
            });

            const data = await res.json();

            if (data.success) {
                alert("Registration successful! Please login.");
                switchAuthMode("login");
            } else {
                alert(data.message || "Registration failed.");
            }
        } else if (currentAuthMode === "login") {
            const password = document.getElementById("auth_password").value;

            const res = await fetch(`${API_URL}/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });

            const data = await res.json();

            if (data.success) {
                currentUser = data.user;

                document.getElementById("displayUserName").innerText =
                    currentUser.full_name;
                document.getElementById("dropdownName").innerText =
                    currentUser.full_name;
                document.getElementById("dropdownRole").innerText =
                    currentUser.role;

                document.getElementById("authModal").style.display = "none";
                document.getElementById("mainContainer").style.opacity = "1";
                document.getElementById("mainContainer").style.pointerEvents = "auto";

                loadReports();
            } else {
                alert(data.message || "Login failed.");
            }
        } else if (currentAuthMode === "forgot") {
            const new_password = document.getElementById("auth_new_password").value;

            const res = await fetch(`${API_URL}/forgot-password`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, new_password })
            });

            const data = await res.json();

            if (data.success) {
                alert("Password reset successful! Please login with your new password.");
                switchAuthMode("login");
            } else {
                alert(data.message || "Password reset failed.");
            }
        }
    } catch (error) {
        console.error("Authentication error:", error);
        alert("Cannot connect to the server. Check whether Flask is running.");
    }
}

function logout() {
    closeChat();

    currentUser = null;
    activeChatSession = null;

    document.getElementById("authModal").style.display = "flex";
    document.getElementById("mainContainer").style.opacity = "0.3";
    document.getElementById("mainContainer").style.pointerEvents = "none";
    document.getElementById("authForm").reset();

    switchAuthMode("register");
}

async function submitReport(event) {
    event.preventDefault();

    if (!currentUser) return;

    const formData = new FormData();

    formData.append("report_type", document.getElementById("report_type").value);
    formData.append("item_name", document.getElementById("item_name").value);
    formData.append("item_category", document.getElementById("item_category").value);
    formData.append("colour", document.getElementById("colour").value);
    formData.append("brand", document.getElementById("brand").value);
    formData.append("description", document.getElementById("description").value);
    formData.append("location", document.getElementById("location").value);
    formData.append("reporter_email", currentUser.email);
    formData.append("reporter_role", currentUser.role);

    const imageFile = document.getElementById("item_image").files[0];

    if (imageFile) {
        formData.append("image", imageFile);
    }

    try {
        const res = await fetch(`${API_URL}/report-item`, {
            method: "POST",
            body: formData
        });

        const data = await res.json();

        if (data.success) {
            alert("Item reported successfully with AI feature extraction!");
            document.getElementById("reportForm").reset();
            loadReports();
        } else {
            alert(data.message || "Error submitting report.");
        }
    } catch (error) {
        console.error("Report error:", error);
        alert("Cannot connect to the server.");
    }
}

async function loadReports() {
    try {
        const res = await fetch(`${API_URL}/reports`);
        const reports = await res.json();
        const feed = document.getElementById("reportsFeed");

        if (reports.length === 0) {
            feed.innerHTML =
                `<p class="empty-state">No items reported yet. Submit a report to see it appear here instantly.</p>`;
            return;
        }

        feed.innerHTML = reports.map(r => `
            <div class="report-item-card">
                <div class="report-badge ${r.report_type}">${r.report_type.toUpperCase()}</div>
                <h3>${r.item_name} (${r.item_category})</h3>
                <p><strong>Location:</strong> ${r.location}</p>
                <p><strong>Colour / Brand:</strong> ${r.colour || "N/A"} / ${r.brand || "N/A"}</p>
                <p><strong>Identities:</strong> ${r.description || "None"}</p>
                <p><strong>Token ID:</strong> ${r.user_token}</p>
                ${r.image_url ? `<img src="${r.image_url}" class="item-thumb" alt="Item">` : ""}
            </div>
        `).join("");
    } catch (error) {
        console.error("Loading reports failed:", error);
    }
}

async function loadMatches() {
    try {
        const res = await fetch(`${API_URL}/match-candidates`);
        const matches = await res.json();
        const feed = document.getElementById("reportsFeed");

        if (matches.length === 0) {
            feed.innerHTML =
                `<p class="empty-state">No AI matches found yet. Report corresponding lost and found items to trigger matches.</p>`;
            return;
        }

        feed.innerHTML = matches.map(m => `
            <div class="match-card">
                <h3>${m.lost_item} ⟷ ${m.found_item}</h3>
                <p><strong>Category:</strong> ${m.category}</p>
                <p><strong>Match Score:</strong> ${m.score}%</p>
                <button type="button"
                    onclick="requestChat('${m.found_token}', '${m.lost_token}', '${String(m.found_item).replace(/'/g, "\\'")}')"
                    class="primary-btn">
                    Request Anonymous Chat
                </button>
            </div>
        `).join("");
    } catch (error) {
        console.error("Loading matches failed:", error);
    }
}

function switchFeedTab(tab, event) {
    document.querySelectorAll(".feed-section .tab-btn")
        .forEach(btn => btn.classList.remove("active"));

    event.target.classList.add("active");

    if (tab === "reports") {
        loadReports();
    } else if (tab === "matches") {
        loadMatches();
    }
}

async function requestChat(finderToken, ownerToken, itemName) {
    try {
        const res = await fetch(`${API_URL}/chat/request`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                finder_token: finderToken,
                owner_token: ownerToken,
                item_name: itemName
            })
        });

        const data = await res.json();

        if (data.success) {
            activeChatSession = {
                finder_token: finderToken,
                owner_token: ownerToken
            };

            openChatModal();
        } else {
            alert(data.message || "Could not initiate chat.");
        }
    } catch (error) {
        console.error("Chat request error:", error);
        alert("Cannot connect to the server.");
    }
}

function openChatModal() {
    document.getElementById("chatModal").style.display = "flex";

    if (chatPollInterval) {
        clearInterval(chatPollInterval);
    }

    pollChatMessages();
    chatPollInterval = setInterval(pollChatMessages, 2000);
}

function closeChat() {
    document.getElementById("chatModal").style.display = "none";

    if (chatPollInterval) {
        clearInterval(chatPollInterval);
        chatPollInterval = null;
    }
}

function getSenderEmail(message) {
    return String(
        message.sender_email ??
        message.senderEmail ??
        message.email ??
        ""
    ).trim().toLowerCase();
}

function appendMessageBubble(chatBox, message, isMine) {
    const bubble = document.createElement("div");
    bubble.className = `chat-msg ${isMine ? "mine" : "theirs"}`;

    const label = document.createElement("strong");
    label.textContent = isMine ? "You" : "Other Person";

    const messageText = document.createElement("span");
    messageText.textContent = String(message.text ?? message.message ?? "");

    bubble.appendChild(label);
    bubble.appendChild(messageText);
    chatBox.appendChild(bubble);
}

async function pollChatMessages() {
    if (!activeChatSession || !currentUser) return;

    try {
        const params = new URLSearchParams({
            token1: activeChatSession.finder_token,
            token2: activeChatSession.owner_token,
            user_email: currentUser.email || ""
        });

        const res = await fetch(`${API_URL}/chat/messages?${params}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const data = await res.json();
        const chatBox = document.getElementById("chatMessages");
        const inputArea = document.getElementById("chatInputArea");

        if (data.authorized === false) {
            if (inputArea) inputArea.style.display = "none";
            chatBox.innerHTML = `
                <div style="text-align: center; padding: 25px; color: #dc2626;">
                    <strong>🔒 Access Restricted</strong>
                    <p style="font-size: 0.85rem; margin-top: 8px; color: #64748b; line-height: 1.4;">
                        This anonymous chat is strictly private between the item owner and finder. You do not have permission to view or participate in this conversation.
                    </p>
                </div>
            `;
            return;
        }

        if (inputArea) inputArea.style.display = "flex";

        const messages = data.messages || [];

        if (!Array.isArray(messages) || messages.length === 0) {
            chatBox.innerHTML = `<p class="empty-state">Start secure conversation...</p>`;
            return;
        }

        chatBox.replaceChildren();

        const myEmail = String(currentUser.email || "").trim().toLowerCase();

        messages.forEach(message => {
            const senderEmail = getSenderEmail(message);
            const isMine = senderEmail !== "" && senderEmail === myEmail;

            appendMessageBubble(chatBox, message, isMine);
        });

        chatBox.scrollTop = chatBox.scrollHeight;
    } catch (error) {
        console.error("Loading chat messages failed:", error);
    }
}

async function sendChatMessage() {
    const textInput = document.getElementById("chatInput");
    const messageText = textInput.value.trim();

    if (!messageText || !activeChatSession || !currentUser) return;

    try {
        const res = await fetch(`${API_URL}/chat/messages`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                token1: activeChatSession.finder_token,
                token2: activeChatSession.owner_token,
                sender_email: currentUser.email,
                text: messageText
            })
        });

        if (!res.ok) {
            throw new Error(`HTTP ${res.status}`);
        }

        textInput.value = "";
        await pollChatMessages();
    } catch (error) {
        console.error("Sending message failed:", error);
        alert("Message could not be sent. Please try again.");
    }
}

const chatInputElement = document.getElementById("chatInput");
if (chatInputElement) {
    chatInputElement.addEventListener("keydown", event => {
        if (event.key === "Enter") {
            event.preventDefault();
            sendChatMessage();
        }
    });
}