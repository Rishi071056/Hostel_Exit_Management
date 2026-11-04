const API = "http://127.0.0.1:8000";

const token = sessionStorage.getItem("hostel_token");
const role = sessionStorage.getItem("hostel_role");

if (!token || role !== "warden") {
    window.location.href = "index.html";
}


// =====================================================
// COMMON API FUNCTION
// =====================================================

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


// =====================================================
// HELPERS
// =====================================================

function getList(data) {
    if (Array.isArray(data)) return data;
    if (Array.isArray(data?.data)) return data.data;
    if (Array.isArray(data?.requests)) return data.requests;
    if (Array.isArray(data?.complaints)) return data.complaints;
    if (Array.isArray(data?.guards)) return data.guards;
    if (Array.isArray(data?.students)) return data.students;
    if (Array.isArray(data?.registrations)) return data.registrations;

    return [];
}


function escapeHTML(value) {
    return String(value ?? "—").replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    })[character]);
}


function showMessage(message, success = true) {
    let element = document.getElementById("wardenMessage");

    if (!element) {
        element = document.createElement("div");
        element.id = "wardenMessage";
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


function formatDate(value) {
    if (!value) return "—";

    const date = new Date(value);

    return Number.isNaN(date.getTime())
        ? "—"
        : date.toLocaleString();
}


// =====================================================
// WARDEN PROFILE
// =====================================================

async function loadWardenProfile() {
    try {
        const data = await apiRequest("/warden/profile");

        const warden = data.warden || data.profile || data;
        const name = warden.name || "Warden";

        document.getElementById("wardenName").textContent = name;
        document.getElementById("welcomeWarden").textContent = name;

    } catch (error) {
        showMessage("Profile: " + error.message, false);
    }
}


// =====================================================
// PENDING STUDENT REGISTRATIONS
// =====================================================

async function loadStudentRegistrations() {
    const table = document.getElementById("pendingRegistrations");

    if (!table) return;

    try {
        const data = await apiRequest("/warden/registrations/pending");

        const registrations = getList(data);

        const countElement = document.getElementById(
            "registrationCount"
        );

        if (countElement) {
            countElement.textContent = registrations.length;
        }

        if (!registrations.length) {
            table.innerHTML = `
                <tr>
                    <td colspan="8">
                        No pending student registrations.
                    </td>
                </tr>
            `;
            return;
        }

        table.innerHTML = registrations.map(student => `
            <tr>
                <td>${escapeHTML(student.roll_no)}</td>
                <td>${escapeHTML(student.name)}</td>
                <td>${escapeHTML(student.email)}</td>
                <td>${escapeHTML(student.phone_number)}</td>
                <td>${escapeHTML(student.hostel)}</td>
                <td>${escapeHTML(student.room_no)}</td>
                <td>${escapeHTML(student.branch)}</td>
                <td>
                    <button
                        class="dashboard-button"
                        onclick="approveStudentRegistration('${escapeHTML(student.roll_no)}')">
                        Approve
                    </button>
                </td>
            </tr>
        `).join("");

    } catch (error) {
        table.innerHTML = `
            <tr>
                <td colspan="8">
                    ${escapeHTML(error.message)}
                </td>
            </tr>
        `;
    }
}


// =====================================================
// APPROVE STUDENT REGISTRATION
// =====================================================

async function approveStudentRegistration(rollNo) {
    if (!confirm(
        `Are you sure you want to approve student ${rollNo}?`
    )) {
        return;
    }

    try {
        await apiRequest(
            `/warden/registrations/${encodeURIComponent(rollNo)}/approve`,
            "POST"
        );

        showMessage(
            `Student ${rollNo} approved successfully!`
        );

        await loadStudentRegistrations();

    } catch (error) {
        showMessage(
            "Student approval failed: " + error.message,
            false
        );
    }
}


// =====================================================
// PENDING EXIT REQUESTS
// =====================================================

async function loadRequests() {
    const table = document.getElementById("wardenRequests");

    try {
        const data = await apiRequest("/warden/requests/pending");

        const requests = getList(data);

        document.getElementById("pendingCount").textContent =
            requests.length;

        if (!requests.length) {
            table.innerHTML =
                '<tr><td colspan="5">No pending exit requests.</td></tr>';
            return;
        }

        table.innerHTML = requests.map(request => {
            const id = Number(request.request_id);

            return `
                <tr>
                    <td>${escapeHTML(request.roll_no)}</td>
                    <td>${escapeHTML(request.destination)}</td>
                    <td>${escapeHTML(request.purpose)}</td>
                    <td>${formatDate(request.expected_return)}</td>
                    <td>
                        <button
                            class="dashboard-button"
                            onclick="approveRequest(${id})">
                            Approve
                        </button>

                        <button
                            class="dashboard-button"
                            style="background:#b83250;margin-left:5px"
                            onclick="rejectRequest(${id})">
                            Reject
                        </button>
                    </td>
                </tr>
            `;
        }).join("");

    } catch (error) {
        table.innerHTML = `
            <tr>
                <td colspan="5">${escapeHTML(error.message)}</td>
            </tr>
        `;
    }
}


// =====================================================
// APPROVE EXIT REQUEST
// =====================================================

async function approveRequest(id) {
    if (!confirm("Approve this student's exit request?")) return;

    try {
        await apiRequest(
            `/warden/requests/${id}/approve`,
            "POST"
        );

        showMessage(`Exit request #${id} approved successfully!`);

        await loadRequests();

    } catch (error) {
        showMessage(
            "Approval failed: " + error.message,
            false
        );
    }
}


// =====================================================
// REJECT EXIT REQUEST
// =====================================================

async function rejectRequest(id) {
    const reason = prompt("Enter the reason for rejection:");

    if (reason === null) return;

    if (!reason.trim()) {
        showMessage("Please enter a rejection reason.", false);
        return;
    }

    try {
        await apiRequest(
            `/warden/requests/${id}/reject`,
            "POST",
            {
                rejection_reason: reason.trim()
            }
        );

        showMessage(`Exit request #${id} rejected successfully!`);

        await loadRequests();

    } catch (error) {
        showMessage(
            "Rejection failed: " + error.message,
            false
        );
    }
}


// =====================================================
// STUDENT COMPLAINTS
// =====================================================

async function loadComplaints() {
    const table = document.getElementById("wardenComplaints");

    try {
        const data = await apiRequest("/warden/complaints");

        const allComplaints = getList(data);

        // Hide complaints that have been resolved
        const complaints = allComplaints.filter(complaint =>
            String(complaint.status || "").trim().toLowerCase() !== "resolved"
        );

        document.getElementById("complaintCount").textContent =
            complaints.length;

        if (!complaints.length) {
            table.innerHTML =
                '<tr><td colspan="5">No pending complaints.</td></tr>';
            return;
        }

        table.innerHTML = complaints.map(complaint => `
            <tr>
                <td>${escapeHTML(complaint.roll_no)}</td>
                <td>${escapeHTML(complaint.category)}</td>
                <td>${escapeHTML(complaint.description)}</td>
                <td>${escapeHTML(complaint.status)}</td>
                <td>
                    <button
                        class="dashboard-button"
                        onclick="updateComplaint(${Number(complaint.id)})">
                        Update
                    </button>
                </td>
            </tr>
        `).join("");

    } catch (error) {
        table.innerHTML = `
            <tr>
                <td colspan="5">${escapeHTML(error.message)}</td>
            </tr>
        `;
    }
}


// =====================================================
// UPDATE COMPLAINT
// =====================================================

async function updateComplaint(id) {
    const status = prompt(
        "Enter status: Pending, In Progress, or Resolved"
    );

    if (status === null) return;

    const validStatuses = [
        "Pending",
        "In Progress",
        "Resolved"
    ];

    if (!validStatuses.includes(status.trim())) {
        showMessage("Please enter a valid complaint status.", false);
        return;
    }

    const response = prompt("Enter your response to the student:");

    if (response === null) return;

    try {
        await apiRequest(
            `/warden/complaints/${id}`,
            "PUT",
            {
                status: status.trim(),
                response: response.trim()
            }
        );

        showMessage(
            status.trim().toLowerCase() === "resolved"
                ? "Complaint resolved and removed from the active complaints list!"
                : "Complaint updated successfully!"
        );

        // Reload complaints immediately
        await loadComplaints();

    } catch (error) {
        showMessage(
            "Complaint update failed: " + error.message,
            false
        );
    }
}


// =====================================================
// PENDING GUARD APPROVALS
// =====================================================

async function loadGuards() {
    const table = document.getElementById("wardenGuards");

    try {
        const data = await apiRequest("/warden/guards/pending");

        const guards = getList(data);

        if (!guards.length) {
            table.innerHTML =
                '<tr><td colspan="4">No pending guard registrations.</td></tr>';
            return;
        }

        table.innerHTML = guards.map(guard => `
            <tr>
                <td>${escapeHTML(guard.guard_id)}</td>
                <td>${escapeHTML(guard.name)}</td>
                <td>${escapeHTML(guard.email)}</td>
                <td>
                    <button
                        class="dashboard-button"
                        onclick="approveGuard(${Number(guard.guard_id)})">
                        Approve
                    </button>
                </td>
            </tr>
        `).join("");

    } catch (error) {
        table.innerHTML = `
            <tr>
                <td colspan="4">${escapeHTML(error.message)}</td>
            </tr>
        `;
    }
}


// =====================================================
// APPROVE GUARD
// =====================================================

async function approveGuard(id) {
    if (!confirm("Approve this guard registration?")) return;

    try {
        await apiRequest(
            `/warden/guards/${id}/approve`,
            "POST"
        );

        showMessage("Guard approved successfully!");

        await loadGuards();

    } catch (error) {
        showMessage(
            "Guard approval failed: " + error.message,
            false
        );
    }
}


// =====================================================
// STUDENTS OUTSIDE
// =====================================================

async function loadOutsideStudents() {
    const table = document.getElementById("outsideStudents");

    try {
        const data = await apiRequest("/warden/students/outside");

        const students = getList(data);

        document.getElementById("outsideCount").textContent =
            students.length;

        if (!students.length) {
            table.innerHTML =
                '<tr><td colspan="4">No students currently outside.</td></tr>';
            return;
        }

        table.innerHTML = students.map(student => `
            <tr>
                <td>${escapeHTML(student.roll_no)}</td>
                <td>${escapeHTML(student.request_id)}</td>
                <td>${formatDate(student.exit_time)}</td>
                <td>${formatDate(student.expected_return)}</td>
            </tr>
        `).join("");

    } catch (error) {
        table.innerHTML = `
            <tr>
                <td colspan="4">${escapeHTML(error.message)}</td>
            </tr>
        `;
    }
}


// =====================================================
// LOGOUT
// =====================================================

function logout() {
    sessionStorage.removeItem("hostel_token");
    sessionStorage.removeItem("hostel_role");
    sessionStorage.removeItem("hostel_email");

    window.location.href = "index.html";
}


// =====================================================
// LOAD DASHBOARD
// =====================================================

async function initializeWardenDashboard() {
    await Promise.all([
        loadWardenProfile(),
        loadStudentRegistrations(),
        loadRequests(),
        loadComplaints(),
        loadGuards(),
        loadOutsideStudents()
    ]);
}

initializeWardenDashboard();