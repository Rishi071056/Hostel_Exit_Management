const API_BASE = "http://127.0.0.1:8000";

let selectedRole = "student";
let cameraStream = null;


// =====================================
// CHANGE LOGIN ROLE
// =====================================

function selectRole(role) {

    selectedRole = role;

    document.querySelectorAll(".role-btn").forEach(button => {
        button.classList.toggle(
            "active",
            button.dataset.role === role
        );
    });

    const label = document.getElementById("identityLabel");
    const identity = document.getElementById("identity");
    const registerText = document.getElementById("registerText");
    const faceLoginSection = document.getElementById("faceLoginSection");

    if (role === "student") {

        label.textContent = "Student Email";
        identity.placeholder = "Enter your registered email";
        faceLoginSection.style.display = "block";

    } else if (role === "warden") {

        label.textContent = "Warden Email";
        identity.placeholder = "Enter your warden email";
        faceLoginSection.style.display = "none";

    } else {

        label.textContent = "Guard Email";
        identity.placeholder = "Enter your guard email";
        faceLoginSection.style.display = "none";
    }

    // Show registration link for ALL roles
    registerText.style.display = "block";

    // Link opens registration page with selected role
    const registerLink = registerText.querySelector("a");

    registerLink.href = `register.html?role=${role}`;

    document.getElementById("loginMessage").textContent = "";
}


// Set default role
selectRole("student");


// =====================================
// SCROLL TO LOGIN
// =====================================

function scrollToLogin() {

    document.getElementById("login").scrollIntoView({
        behavior: "smooth"
    });

}


// =====================================
// PASSWORD LOGIN
// =====================================

document.getElementById("loginForm").addEventListener("submit", async function(event) {

    event.preventDefault();

    const email = document.getElementById("identity").value.trim();
    const password = document.getElementById("password").value;

    const message = document.getElementById("loginMessage");
    const loginButton = document.querySelector(".login-submit");

    if (!email || !password) {
        message.textContent = "Please enter your email and password.";
        return;
    }

    let endpoint = "";

    if (selectedRole === "student") {
        endpoint = "/login-password";
    } else if (selectedRole === "warden") {
        endpoint = "/warden/login";
    } else {
        endpoint = "/guard/login";
    }

    loginButton.disabled = true;
    loginButton.textContent = "Signing in...";

    message.style.color = "#c4b5fd";
    message.textContent = "Checking your credentials...";

    try {

        const response = await fetch(API_BASE + endpoint, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                email: email,
                password: password
            })

        });

        const data = await response.json();

        if (!response.ok || data.error) {
            throw new Error(
                data.detail || data.error || "Login failed."
            );
        }

        const token = data.access_token || data.token;

        if (!token) {
            throw new Error(
                "Login succeeded but no access token was returned."
            );
        }

        sessionStorage.setItem("hostel_token", token);
        sessionStorage.setItem("hostel_role", selectedRole);
        sessionStorage.setItem("hostel_email", email);

        message.style.color = "#86efac";
        message.textContent = "Login successful! Welcome.";

        setTimeout(() => {

            if (selectedRole === "student") {
                window.location.href = "student-dashboard.html";
            } else if (selectedRole === "warden") {
                window.location.href = "warden-dashboard.html";
            } else {
                window.location.href = "guard-dashboard.html";
            }

        }, 700);

    } catch (error) {

        message.style.color = "#fca5a5";
        message.textContent = error.message;

    } finally {

        loginButton.disabled = false;
        loginButton.innerHTML = 'Sign In <span>→</span>';

    }

});


// =====================================
// STUDENT FACE LOGIN
// =====================================

async function startFaceLogin() {

    if (selectedRole !== "student") return;

    const modal = document.createElement("div");

    modal.id = "faceCameraModal";

    modal.style.cssText = `
        position: fixed;
        inset: 0;
        background: rgba(10, 10, 25, 0.88);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 99999;
        padding: 20px;
    `;

    modal.innerHTML = `
        <div style="
            background: white;
            color: #222;
            width: 100%;
            max-width: 430px;
            padding: 25px;
            border-radius: 18px;
            text-align: center;
            font-family: Inter, sans-serif;
        ">

            <h2 style="color: #5425a8;">Student Face Login</h2>

            <p style="color: #666;">
                Position your face inside the camera.
            </p>

            <video
                id="faceVideo"
                autoplay
                playsinline
                style="
                    width: 100%;
                    max-height: 300px;
                    object-fit: cover;
                    border-radius: 12px;
                    background: #222;
                "
            ></video>

            <canvas id="faceCanvas" style="display:none;"></canvas>

            <p id="faceCameraMessage" style="
                color: #666;
                font-size: 14px;
                margin: 12px 0;
            ">Starting camera...</p>

            <button id="captureFaceButton" disabled style="
                width: 100%;
                padding: 13px;
                border: none;
                border-radius: 10px;
                background: linear-gradient(135deg, #7138d4, #4f46e5);
                color: white;
                font-size: 15px;
                font-weight: 600;
                cursor: pointer;
                margin-bottom: 10px;
            ">Capture Face</button>

            <button id="closeFaceButton" style="
                width: 100%;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 10px;
                background: white;
                color: #444;
                cursor: pointer;
            ">Cancel</button>

        </div>
    `;

    document.body.appendChild(modal);

    const video = document.getElementById("faceVideo");
    const canvas = document.getElementById("faceCanvas");
    const captureButton = document.getElementById("captureFaceButton");
    const closeButton = document.getElementById("closeFaceButton");
    const status = document.getElementById("faceCameraMessage");

    let isClosed = false;

    function closeCamera() {

        isClosed = true;

        if (cameraStream) {
            cameraStream.getTracks().forEach(track => track.stop());
            cameraStream = null;
        }

        modal.remove();
    }

    closeButton.addEventListener("click", closeCamera);

    try {

        if (!navigator.mediaDevices ||
            !navigator.mediaDevices.getUserMedia) {

            throw new Error(
                "Camera is unavailable. Open the website using localhost or HTTPS."
            );
        }

        cameraStream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: "user"
            },
            audio: false
        });

        if (isClosed) {
            cameraStream.getTracks().forEach(track => track.stop());
            cameraStream = null;
            return;
        }

        video.srcObject = cameraStream;
        await video.play();

        status.textContent =
            "Camera ready. Position your face and capture.";

        captureButton.disabled = false;

    } catch (error) {

        status.style.color = "red";
        status.textContent = "Camera error: " + error.message;

        return;
    }


    // CAPTURE AND VERIFY FACE

    captureButton.addEventListener("click", async function() {

        if (selectedRole !== "student" || isClosed) return;

        if (!video.videoWidth || !video.videoHeight) {
            status.textContent = "Camera is not ready. Try again.";
            return;
        }

        captureButton.disabled = true;
        closeButton.disabled = true;

        status.style.color = "#5425a8";
        status.textContent = "Capturing face...";

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const context = canvas.getContext("2d");

        context.drawImage(
            video,
            0,
            0,
            canvas.width,
            canvas.height
        );

        canvas.toBlob(async function(blob) {

            if (!blob) {

                status.textContent =
                    "Could not capture image. Please try again.";

                captureButton.disabled = false;
                closeButton.disabled = false;

                return;
            }

            if (cameraStream) {
                cameraStream.getTracks().forEach(track => track.stop());
                cameraStream = null;
            }

            status.textContent = "Verifying your face...";

            try {

                const formData = new FormData();

                formData.append(
                    "image",
                    blob,
                    "student_face.jpg"
                );

                const response = await fetch(
                    API_BASE + "/login-face",
                    {
                        method: "POST",
                        body: formData
                    }
                );

                const data = await response.json();

                if (!response.ok || data.error) {
                    throw new Error(
                        data.detail ||
                        data.error ||
                        "Face verification failed."
                    );
                }

                const token = data.access_token || data.token;

                if (!token) {
                    throw new Error(
                        "No authentication token was returned."
                    );
                }

                sessionStorage.setItem("hostel_token", token);
                sessionStorage.setItem("hostel_role", "student");
                sessionStorage.setItem("hostel_email", data.email || "");

                status.style.color = "green";
                status.textContent =
                    "Face verified successfully! Logging in...";

                setTimeout(() => {
                    window.location.href = "student-dashboard.html";
                }, 1000);

            } catch (error) {

                status.style.color = "red";
                status.textContent = error.message;

                captureButton.disabled = false;
                closeButton.disabled = false;
            }

        }, "image/jpeg", 0.9);

    });

}


// =====================================
// REGISTRATION
// =====================================

function showRegistration() {

    window.location.href = `register.html?role=${selectedRole}`;

}