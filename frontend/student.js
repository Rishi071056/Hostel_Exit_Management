
const API = "http://127.0.0.1:8000";

const token = sessionStorage.getItem("hostel_token");
const role = sessionStorage.getItem("hostel_role");

if (!token || role !== "student") {
    window.location.href = "index.html";
}

let studentRequests = [];
let studentComplaints = [];


// API helper
async function apiRequest(endpoint, method = "GET", body = null) {
    const options = {
        method,
        headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        }
    };

    if (body !== null) {
        options.body = JSON.stringify(body);
    }

    const response = await fetch(API + endpoint, options);

    let data = {};
    try {
        data = await response.json();
    } catch {
        data = {};
    }

    if (!response.ok) {
        throw new Error(
            data.detail || data.error || `Request failed (${response.status})`
        );
    }

    return data;
}


// Show messages
function showMessage(message, success = true) {
    let element = document.getElementById("studentMessage");

    if (!element) {
        element = document.createElement("div");
        element.id = "studentMessage";
        element.style.cssText =
            "padding:12px;margin:15px 0;border-radius:10px;font-size:13px;";
        document.querySelector(".dashboard-main").prepend(element);
    }

    element.textContent = message;
    element.style.color = success ? "#86efac" : "#fca5a5";
    element.style.background = success
        ? "rgba(34,197,94,0.1)"
        : "rgba(239,68,68,0.1)";
}


// Normalize API lists
function getList(data) {
    if (Array.isArray(data)) return data;

    if (data && Array.isArray(data.data)) return data.data;
    if (data && Array.isArray(data.requests)) return data.requests;
    if (data && Array.isArray(data.complaints)) return data.complaints;

    return [];
}


// Load profile
async function loadProfile() {
    try {
        const data = await apiRequest("/profile");
        const profile = data.student || data.profile || data;

        const name = profile.name || "Student";
        const roll = profile.roll_no || "Student Account";

        document.getElementById("welcomeName").textContent = name;
        document.getElementById("sidebarName").textContent = name;
        document.getElementById("sidebarRoll").textContent = roll;

        const fields = {
            "Name": profile.name,
            "Roll Number": profile.roll_no,
            "Email": profile.email,
            "Hostel": profile.hostel,
            "Room Number": profile.room_no,
            "Branch": profile.branch,
            "Year": profile.year
        };

        document.getElementById("profileDetails").innerHTML =
            Object.entries(fields)
                .map(([label, value]) => `
                    <div class="profile-item">
                        <span>${escapeHTML(label)}</span>
                        <strong>${escapeHTML(value ?? "Not available")}</strong>
                    </div>
                `).join("");

    } catch (error) {
        showMessage("Could not load profile: " + error.message, false);
    }
}


// DISPLAY DIGITAL EXIT RECEIPTS
function displayDigitalReceipts() {
    const container = document.getElementById("activeReceiptContainer");

    if (!container) return;

    // Only show receipts for students currently outside
    const activeReceipts = studentRequests.filter(request =>
        String(request.current_status || "").toLowerCase() === "outside" &&
        request.receipt_number
    );

    if (!activeReceipts.length) {
        container.innerHTML = `
            <div style="
                background:#f5f3ff;
                padding:25px;
                border-radius:14px;
                text-align:center;
                border:1px dashed #c4b5fd;
            ">
                <div style="font-size:38px;">🎫</div>

                <h3 style="color:#4338ca;margin:10px 0;">
                    No Active Exit Receipt
                </h3>

                <p style="color:#64748b;">
                    Your digital receipt will appear here after the guard
                    marks your exit.
                </p>
            </div>
        `;
        return;
    }

    container.innerHTML = activeReceipts.map(request => `
        <div style="
            background:linear-gradient(135deg,#eef2ff,#f5f3ff);
            border:2px solid #a5b4fc;
            border-radius:16px;
            padding:24px;
            margin-bottom:18px;
        ">

            <div style="
                display:flex;
                justify-content:space-between;
                align-items:center;
                flex-wrap:wrap;
                gap:10px;
            ">
                <h3 style="color:#4338ca;margin:0;">
                    🎫 Digital Exit Pass
                </h3>

                <span style="
                    background:#dcfce7;
                    color:#15803d;
                    padding:6px 12px;
                    border-radius:20px;
                    font-size:12px;
                    font-weight:700;
                ">
                    ACTIVE
                </span>
            </div>


            <!-- RECEIPT NUMBER -->
            <div style="
                text-align:center;
                background:white;
                border:1px dashed #818cf8;
                border-radius:12px;
                padding:22px;
                margin-top:18px;
            ">
                <p style="color:#64748b;margin:0 0 8px;">
                    YOUR RECEIPT NUMBER
                </p>

                <h2 style="
                    color:#4338ca;
                    font-size:25px;
                    letter-spacing:1px;
                    margin:0;
                    overflow-wrap:anywhere;
                ">
                    ${escapeHTML(request.receipt_number)}
                </h2>

                <button
                    class="dashboard-button"
                    style="margin-top:15px;"
                    onclick="copyReceipt('${escapeHTML(request.receipt_number)}')">

                    Copy Receipt Number
                </button>
            </div>


            <!-- BASIC EXIT INFORMATION -->
            <div style="
                display:grid;
                grid-template-columns:repeat(auto-fit,minmax(130px,1fr));
                gap:15px;
                margin-top:18px;
            ">
                <div>
                    <small style="color:#64748b;">Request ID</small>
                    <p style="font-weight:700;margin:5px 0;color:#334155;">
                        #${escapeHTML(request.request_id)}
                    </p>
                </div>

                <div>
                    <small style="color:#64748b;">Destination</small>
                    <p style="font-weight:700;margin:5px 0;color:#334155;">
                        ${escapeHTML(request.destination || "—")}
                    </p>
                </div>

                <div>
                    <small style="color:#64748b;">Exit Time</small>
                    <p style="font-weight:700;margin:5px 0;color:#334155;">
                        ${escapeHTML(formatDate(request.exit_time))}
                    </p>
                </div>
            </div>


            <!-- ADDITIONAL EXIT DETAILS -->
            <div style="
                background:white;
                padding:18px;
                border-radius:12px;
                margin-top:18px;
                color:#334155;
                border:1px solid #e0e7ff;
            ">
                <h3 style="color:#4338ca;margin:0 0 15px;">
                    📋 Exit Details
                </h3>

                <div style="margin-bottom:12px;">
                    <small style="color:#64748b;">Student Name</small>
                    <p style="font-weight:700;margin:5px 0;">
                        ${escapeHTML(request.name || request.student_name || "—")}
                    </p>
                </div>

                <div style="margin-bottom:12px;">
                    <small style="color:#64748b;">Roll Number</small>
                    <p style="font-weight:700;margin:5px 0;">
                        ${escapeHTML(request.roll_no || "—")}
                    </p>
                </div>

                <div style="margin-bottom:12px;">
                    <small style="color:#64748b;">Purpose</small>
                    <p style="font-weight:700;margin:5px 0;">
                        ${escapeHTML(request.purpose || "—")}
                    </p>
                </div>

                <div style="margin-bottom:12px;">
                    <small style="color:#64748b;">Expected Return</small>
                    <p style="font-weight:700;margin:5px 0;">
                        ${escapeHTML(formatDate(request.expected_return))}
                    </p>
                </div>

                <div>
                    <small style="color:#64748b;">Approval Status</small>
                    <p style="
                        font-weight:700;
                        margin:5px 0;
                        color:#15803d;
                    ">
                        ${escapeHTML(request.approval_status || "Approved")}
                    </p>
                </div>
            </div>


            <!-- INSTRUCTIONS -->
            <p style="
                color:#4338ca;
                background:#e0e7ff;
                padding:14px;
                border-radius:9px;
                margin:18px 0 0;
                font-size:13px;
                line-height:1.6;
            ">
                📌 Keep this digital receipt safe. Show your receipt number
                to the guard when returning to the hostel.

                Your active receipt will disappear after your return is verified.
            </p>

        </div>
    `).join("");
}


// Copy receipt number
async function copyReceipt(receiptNumber) {
    try {
        await navigator.clipboard.writeText(receiptNumber);
        showMessage("Receipt number copied successfully!");
    } catch (error) {
        prompt("Copy your receipt number:", receiptNumber);
    }
}


// Load exit requests
async function loadRequests() {
    try {
        const data = await apiRequest("/exit-requests");
        studentRequests = getList(data);

        document.getElementById("totalRequests").textContent =
            studentRequests.length;

        document.getElementById("pendingRequests").textContent =
            studentRequests.filter(request =>
                String(request.approval_status || request.status || "")
                    .toLowerCase() === "pending"
            ).length;

        // Update digital receipt whenever requests are loaded
        displayDigitalReceipts();

        const table = document.getElementById("requestsTable");

        if (!studentRequests.length) {
            table.innerHTML =
                '<tr><td colspan="4">No exit requests yet.</td></tr>';
            return;
        }

        table.innerHTML = studentRequests.map(request => {
            const status = request.approval_status ||
                request.status || "Pending";

            const requestId = request.id ?? request.request_id;

            return `
                <tr>
                    <td>${escapeHTML(request.purpose || "—")}</td>

                    <td>${formatDate(
                        request.exit_time ||
                        request.expected_return ||
                        request.request_time
                    )}</td>

                    <td>${escapeHTML(status)}</td>

                    <td>
                        ${String(status).toLowerCase() === "pending"
                            ? `<button class="dashboard-button"
                                onclick="cancelRequest(${Number(requestId)})">
                                Cancel
                               </button>`
                            : "—"}
                    </td>
                </tr>
            `;
        }).join("");

    } catch (error) {
        document.getElementById("requestsTable").innerHTML =
            `<tr><td colspan="4">${escapeHTML(error.message)}</td></tr>`;

        const receiptContainer =
            document.getElementById("activeReceiptContainer");

        if (receiptContainer) {
            receiptContainer.innerHTML =
                `<p>Could not load receipt: ${escapeHTML(error.message)}</p>`;
        }
    }
}


// Submit exit request
document.getElementById("exitForm").addEventListener("submit", async event => {
    event.preventDefault();

    const destination =
        document.getElementById("exitDestination").value.trim();

    const purpose =
        document.getElementById("exitPurpose").value.trim();

    const expectedReturn =
        document.getElementById("returnTime").value;

    if (!destination || !purpose || !expectedReturn) {
        showMessage("Please fill in all exit request fields.", false);
        return;
    }

    try {
        await apiRequest("/exit-requests", "POST", {
            destination,
            purpose,
            expected_return: new Date(expectedReturn).toISOString()
        });

        showMessage("Exit request submitted successfully!");

        event.target.reset();
        event.target.classList.add("hidden");

        await loadRequests();

    } catch (error) {
        showMessage("Could not submit request: " + error.message, false);
    }
});


// Cancel exit request
async function cancelRequest(id) {
    if (!Number.isInteger(id) || id <= 0) {
        showMessage("Invalid request ID.", false);
        return;
    }

    if (!confirm("Are you sure you want to cancel this request?")) return;

    try {
        await apiRequest(`/exit-requests/${id}`, "DELETE");

        showMessage("Exit request cancelled.");

        await loadRequests();

    } catch (error) {
        showMessage("Could not cancel request: " + error.message, false);
    }
}


// Load complaints
async function loadComplaints() {
    try {
        const data = await apiRequest("/complaints");
        studentComplaints = getList(data);

        document.getElementById("totalComplaints").textContent =
            studentComplaints.length;

        const table = document.getElementById("complaintsTable");

        if (!studentComplaints.length) {
            table.innerHTML =
                '<tr><td colspan="4">No complaints submitted yet.</td></tr>';
            return;
        }

        table.innerHTML = studentComplaints.map(complaint => `
            <tr>
                <td>${escapeHTML(complaint.category || "—")}</td>
                <td>${escapeHTML(complaint.description || "—")}</td>
                <td>${escapeHTML(complaint.status || "Pending")}</td>
                <td>${escapeHTML(complaint.response || "Awaiting response")}</td>
            </tr>
        `).join("");

    } catch (error) {
        document.getElementById("complaintsTable").innerHTML =
            `<tr><td colspan="4">${escapeHTML(error.message)}</td></tr>`;
    }
}


// Submit complaint
document.getElementById("complaintForm").addEventListener("submit", async event => {
    event.preventDefault();

    const category =
        document.getElementById("complaintCategory").value;

    const description =
        document.getElementById("complaintDescription").value.trim();

    if (!category || !description) {
        showMessage("Please complete the complaint form.", false);
        return;
    }

    try {
        await apiRequest("/complaints", "POST", {
            category,
            description
        });

        showMessage("Complaint submitted successfully!");

        event.target.reset();
        event.target.classList.add("hidden");

        await loadComplaints();

    } catch (error) {
        showMessage("Could not submit complaint: " + error.message, false);
    }
});


// Show and hide forms
function showExitForm() {
    document.getElementById("exitForm").classList.toggle("hidden");
}

function showComplaintForm() {
    document.getElementById("complaintForm").classList.toggle("hidden");
}


// Navigate to dashboard sections
function openSection(id) {
    document.getElementById(id).scrollIntoView({
        behavior: "smooth"
    });
}


// Logout
function logout() {
    sessionStorage.removeItem("hostel_token");
    sessionStorage.removeItem("hostel_role");
    sessionStorage.removeItem("hostel_email");

    window.location.href = "index.html";
}


// Format date in Indian Standard Time
function formatDate(value) {
    if (!value) return "—";

    let dateValue = value;

    // Treat timestamps without timezone as UTC
    if (
        typeof value === "string" &&
        !value.endsWith("Z") &&
        !/[+-]\d{2}:\d{2}$/.test(value)
    ) {
        dateValue = value.replace(" ", "T") + "Z";
    }

    const date = new Date(dateValue);

    if (Number.isNaN(date.getTime())) return "—";

    return date.toLocaleString("en-IN", {
        timeZone: "Asia/Kolkata",
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: true
    });
}


// Escape text before inserting API data into HTML
function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    })[character]);
}


// Load everything when dashboard opens
async function initializeDashboard() {
    await Promise.all([
        loadProfile(),
        loadRequests(),
        loadComplaints()
    ]);
}

initializeDashboard();


// Refresh receipt and exit requests every 15 seconds
setInterval(() => {
    loadRequests();
}, 15000);
