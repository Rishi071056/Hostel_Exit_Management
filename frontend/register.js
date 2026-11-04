const API_BASE = "http://127.0.0.1:8000";

let selectedRole = "student";
let photoPreviewURL = null;

const registerForm = document.getElementById("registerForm");
const registerMessage = document.getElementById("registerMessage");
const registerButton = document.getElementById("registerButton");

const imageInput = document.getElementById("image");
const photoPreviewBox = document.getElementById("photoPreviewBox");
const photoPreview = document.getElementById("photoPreview");
const photoFileName = document.getElementById("photoFileName");


// ------------------------------------
// ROLE SELECTION
// ------------------------------------

function selectRegisterRole(role) {

    if (!["student", "warden", "guard"].includes(role)) {
        role = "student";
    }

    selectedRole = role;

    document.querySelectorAll(".role-options button").forEach(button => {
        button.classList.toggle(
            "active",
            button.dataset.role === role
        );
    });

    const studentFields = [
        "rollField",
        "hostelField",
        "roomField",
        "branchField",
        "yearField",
        "phoneField",
        "photoField"
    ];

    studentFields.forEach(id => {
        document.getElementById(id).style.display =
            role === "student" ? "flex" : "none";
    });

    document.getElementById("roll_no").required =
        role === "student";

    document.getElementById("hostel").required =
        role === "student";

    document.getElementById("room_no").required =
        role === "student";

    document.getElementById("branch").required =
        role === "student";

    document.getElementById("year").required =
        role === "student";

    document.getElementById("phone_number").required =
        role === "student";

    imageInput.required = role === "student";

    if (role !== "student") {
        imageInput.value = "";
        photoPreviewBox.style.display = "none";
        photoPreview.removeAttribute("src");
    }

    registerMessage.textContent = "";
}


// ------------------------------------
// PHOTO PREVIEW
// ------------------------------------

imageInput.addEventListener("change", function () {

    const file = this.files[0];

    if (photoPreviewURL) {
        URL.revokeObjectURL(photoPreviewURL);
        photoPreviewURL = null;
    }

    if (!file) {
        photoPreviewBox.style.display = "none";
        photoPreview.removeAttribute("src");
        photoFileName.textContent = "";
        return;
    }

    if (!file.type.startsWith("image/")) {
        alert("Please select a valid image file.");
        imageInput.value = "";
        photoPreviewBox.style.display = "none";
        return;
    }

    if (file.size > 5 * 1024 * 1024) {
        alert("Please select an image smaller than 5 MB.");
        imageInput.value = "";
        photoPreviewBox.style.display = "none";
        return;
    }

    photoPreviewURL = URL.createObjectURL(file);

    photoPreview.src = photoPreviewURL;
    photoFileName.textContent = file.name;

    photoPreviewBox.style.display = "flex";
});


// ------------------------------------
// API REQUEST
// ------------------------------------

async function apiRequest(endpoint, options = {}) {

    const response = await fetch(`${API_BASE}${endpoint}`, options);

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(
            data.detail || data.error || "Something went wrong."
        );
    }

    return data;
}


// ------------------------------------
// STUDENT REGISTRATION
// ------------------------------------

async function registerStudent() {

    const formData = new FormData();

    formData.append("roll_no", document.getElementById("roll_no").value.trim());
    formData.append("name", document.getElementById("name").value.trim());
    formData.append("email", document.getElementById("email").value.trim());
    formData.append("hostel", document.getElementById("hostel").value.trim());
    formData.append("room_no", document.getElementById("room_no").value.trim());
    formData.append("branch", document.getElementById("branch").value.trim());
    formData.append("year", document.getElementById("year").value);
    formData.append("phone_number", document.getElementById("phone_number").value.trim());
    formData.append("password", document.getElementById("password").value);

    const imageFile = imageInput.files[0];

    if (!imageFile) {
        throw new Error("Please select your face photo.");
    }

    formData.append("image", imageFile);

    const data = await apiRequest("/register", {
        method: "POST",
        body: formData
    });

    alert(data.message || "Student registration successful.");

    const otp = prompt(
        "Enter the OTP sent to your registered email:"
    );

    if (!otp || !otp.trim()) {
        registerMessage.textContent =
            "Registration submitted. Verify your email to complete registration.";
        return;
    }

    const verificationData = await apiRequest("/verify-email", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            email: document.getElementById("email").value.trim(),
            otp: otp.trim()
        })
    });

    alert(
        verificationData.message ||
        "Student email verified successfully! Your account is waiting for Warden approval."
    );

    window.location.href = "index.html";
}


// ------------------------------------
// WARDEN REGISTRATION
// ------------------------------------

async function registerWarden() {

    const body = {
        name: document.getElementById("name").value.trim(),
        email: document.getElementById("email").value.trim(),
        password: document.getElementById("password").value
    };

    const data = await apiRequest("/warden/register", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(body)
    });

    alert(data.message || "Warden registration successful.");

    const otp = prompt(
        "Enter the OTP sent to your registered email:"
    );

    if (!otp || !otp.trim()) {
        registerMessage.textContent =
            "Registration submitted. Please verify your email.";
        return;
    }

    const verificationData = await apiRequest(
        "/warden/verify-email",
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email: body.email,
                otp: otp.trim()
            })
        }
    );

    alert(
        verificationData.message ||
        "Warden email verified successfully! You can now log in."
    );

    window.location.href = "index.html";
}


// ------------------------------------
// GUARD REGISTRATION
// ------------------------------------

async function registerGuard() {

    const body = {
        name: document.getElementById("name").value.trim(),
        email: document.getElementById("email").value.trim(),
        password: document.getElementById("password").value
    };

    const data = await apiRequest("/guard/register", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(body)
    });

    alert(
        data.message ||
        "Guard registration submitted. Please wait for Warden approval."
    );

    window.location.href = "index.html";
}


// ------------------------------------
// FORM SUBMISSION
// ------------------------------------

registerForm.addEventListener("submit", async function (event) {

    event.preventDefault();

    registerMessage.textContent = "";

    registerButton.disabled = true;
    registerButton.textContent = "Creating Account...";

    try {

        if (selectedRole === "student") {
            await registerStudent();
        }

        else if (selectedRole === "warden") {
            await registerWarden();
        }

        else if (selectedRole === "guard") {
            await registerGuard();
        }

    } catch (error) {

        console.error("Registration error:", error);

        registerMessage.textContent = error.message;
        registerMessage.style.color = "red";

    } finally {

        registerButton.disabled = false;
        registerButton.textContent = "Create Account";

    }
});


// ------------------------------------
// AUTOMATIC ROLE FROM LOGIN PAGE
// ------------------------------------

const urlParams = new URLSearchParams(window.location.search);
const requestedRole = urlParams.get("role");

if (requestedRole && ["student", "warden", "guard"].includes(requestedRole)) {
    selectRegisterRole(requestedRole);
} else {
    selectRegisterRole("student");
}