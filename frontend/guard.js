
const API_BASE = "http://127.0.0.1:8000";

const token = sessionStorage.getItem("hostel_token");
const role = sessionStorage.getItem("hostel_role");

if (!token || role !== "guard") {
    window.location.href = "index.html";
}

const headers = {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
};

async function apiRequest(endpoint, options = {}) {
    const response = await fetch(API_BASE + endpoint, {
        ...options,
        headers: {
            ...headers,
            ...(options.headers || {})
        }
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || data.error || "Request failed");
    }

    return data;
}

function getRows(data) {
    if (Array.isArray(data)) return data;
    if (Array.isArray(data?.data)) return data.data;
    if (Array.isArray(data?.requests)) return data.requests;
    if (Array.isArray(data?.students)) return data.students;
    return [];
}

function safe(value) {
    return String(value ?? "-").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[char]);
}


function formatDate(value) {
    if (!value) return "-";

    // Treat timestamps without timezone information as UTC
    let dateValue = value;

    if (
        typeof value === "string" &&
        !value.endsWith("Z") &&
        !/[+-]\d{2}:\d{2}$/.test(value)
    ) {
        dateValue = value.replace(" ", "T") + "Z";
    }

    const date = new Date(dateValue);

    if (Number.isNaN(date.getTime())) return safe(value);

    return date.toLocaleString("en-IN", {
        timeZone: "Asia/Kolkata",
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: true
    });
}



function showMessage(message, success = true) {
    const element = document.getElementById("requestMessage");
    element.textContent = message;
    element.style.color = success ? "#15803d" : "#dc2626";
}

// Load guard profile
async function loadGuardProfile() {
    try {
        const data = await apiRequest("/guard/profile");
        document.getElementById("guardEmail").textContent =
            data.guard?.email || sessionStorage.getItem("hostel_email") || "";
    } catch (error) {
        showMessage(error.message, false);
    }
}

// Load approved exit requests
async function loadApprovedRequests() {
    const table = document.getElementById("approvedRequestsTable");

    try {
        const data = await apiRequest("/guard/requests/approved");
        const requests = getRows(data);

        document.getElementById("approvedCount").textContent = requests.length;

        if (!requests.length) {
            table.innerHTML = `
                <tr><td colspan="5">No approved requests available.</td></tr>
            `;
            return;
        }

        table.innerHTML = requests.map(request => {
            const id = request.request_id;
            const student = request.name || request.student_name || request.roll_no;

            return `
                <tr>
                    <td>#${safe(id)}</td>
                    <td>${safe(student)}</td>
                    <td>${safe(request.destination)}</td>
                    <td>${safe(formatDate(request.expected_return))}</td>
                    <td>
                        <button class="action-btn"
                            onclick="markExit(${Number(id)})">
                            Mark Exit
                        </button>
                    </td>
                </tr>
            `;
        }).join("");

    } catch (error) {
        table.innerHTML = `
            <tr><td colspan="5">${safe(error.message)}</td></tr>
        `;
    }
}

// Mark student exit
async function markExit(requestId) {
    if (!confirm("Are you sure you want to mark this student as exited?")) {
        return;
    }

    try {
        const data = await apiRequest(
            `/guard/requests/${requestId}/exit`,
            { method: "POST" }
        );

        showMessage(data.message || "Student exit marked successfully.");
        await refreshDashboard();

    } catch (error) {
        showMessage(error.message, false);
    }
}

// Load students currently outside
async function loadOutsideStudents() {
    const table = document.getElementById("outsideStudentsTable");

    try {
        const data = await apiRequest("/guard/students/outside");
        const students = getRows(data);

        document.getElementById("outsideCount").textContent =
            students.length;

        if (!students.length) {
            table.innerHTML = `
                <tr><td colspan="5">No students are currently outside.</td></tr>
            `;
            return;
        }

        table.innerHTML = students.map(student => {
            const id = student.request_id;
            const name = student.name || student.student_name || student.roll_no;

            return `
                <tr>
                    <td>#${safe(id)}</td>
                    <td>${safe(name)}</td>
                    <td>${safe(student.destination)}</td>
                    <td>${safe(formatDate(student.exit_time))}</td>
                    <td>
                        <button class="action-btn return-btn"
                            onclick="markReturn(${Number(id)})">
                            Mark Return
                        </button>
                    </td>
                </tr>
            `;
        }).join("");

    } catch (error) {
        table.innerHTML = `
            <tr><td colspan="5">${safe(error.message)}</td></tr>
        `;
    }
}

// Mark student return
async function markReturn(requestId) {
    const receiptNumber = prompt(
        "Enter the receipt number shown by the student:"
    );

    if (!receiptNumber || !receiptNumber.trim()) {
        return;
    }

    if (!confirm("Verify this receipt and mark the student as returned?")) {
        return;
    }

    try {
        const data = await apiRequest(
            `/guard/requests/${requestId}/return`,
            {
                method: "POST",
                body: JSON.stringify({
                    receipt_number: receiptNumber.trim()
                })
            }
        );

        showMessage(data.message || "Student return verified successfully.");
        await refreshDashboard();

    } catch (error) {
        showMessage(error.message, false);
    }
}

// Load today's exits
async function loadTodayExits() {
    const table = document.getElementById("todayExitsTable");

    try {
        const data = await apiRequest("/guard/exits/today");
        const records = getRows(data);

        document.getElementById("todayExitCount").textContent =
            records.length;

        table.innerHTML = records.length
            ? records.map(record => `
                <tr>
                    <td>#${safe(record.request_id)}</td>
                    <td>${safe(record.name || record.student_name || record.roll_no)}</td>
                    <td>${safe(record.destination)}</td>
                    <td>${safe(formatDate(record.exit_time))}</td>
                </tr>
            `).join("")
            : `<tr><td colspan="4">No exits recorded today.</td></tr>`;

    } catch (error) {
        table.innerHTML = `
            <tr><td colspan="4">${safe(error.message)}</td></tr>
        `;
    }
}

// Load today's returns
async function loadTodayReturns() {
    const table = document.getElementById("todayReturnsTable");

    try {
        const data = await apiRequest("/guard/returns/today");
        const records = getRows(data);

        table.innerHTML = records.length
            ? records.map(record => `
                <tr>
                    <td>#${safe(record.request_id)}</td>
                    <td>${safe(record.name || record.student_name || record.roll_no)}</td>
                    <td>${safe(record.destination)}</td>
                    <td>${safe(formatDate(record.return_time))}</td>
                </tr>
            `).join("")
            : `<tr><td colspan="4">No returns recorded today.</td></tr>`;

    } catch (error) {
        table.innerHTML = `
            <tr><td colspan="4">${safe(error.message)}</td></tr>
        `;
    }
}

// Refresh all dashboard data
async function refreshDashboard() {
    await Promise.all([
        loadApprovedRequests(),
        loadOutsideStudents(),
        loadTodayExits(),
        loadTodayReturns()
    ]);
}

// Logout
function guardLogout() {
    sessionStorage.removeItem("hostel_token");
    sessionStorage.removeItem("hostel_role");
    sessionStorage.removeItem("hostel_email");
    window.location.href = "index.html";
}

// Start dashboard
loadGuardProfile();
refreshDashboard();
