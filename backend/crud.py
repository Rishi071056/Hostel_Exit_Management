from backend.database import supabase
from backend.auth import hash_pass, verify_pass, create_access_token
from backend.services.otp_services import (
    generate_email_otp,
    generate_otp_expiry,
    is_otp_expired
)
from backend.services.email_services import send_email_otp
from fastapi import HTTPException
from datetime import datetime, timezone
import face_recognition
from backend.face_utils import generate_face_embedding
import numpy as np


# =========================================================
# COMMON FUNCTIONS
# =========================================================

def get_all_students():
    response = (
        supabase.table("students")
        .select("roll_no, name, email, hostel, room_no, branch, year")
        .execute()
    )
    return response.data


def check_duplicate(table, column, value):
    response = (
        supabase.table(table)
        .select(column)
        .eq(column, value)
        .execute()
    )
    return len(response.data) > 0


# =========================================================
# STUDENT REGISTRATION - OTP STAGE
# =========================================================

def create_pending_registration(student, image_bytes: bytes):

    duplicate_fields = [
        ("roll_no", student.roll_no, "Roll number"),
        ("email", student.email, "Email"),
        ("phone_number", student.phone_number, "Phone number")
    ]

    for column, value, label in duplicate_fields:

        if check_duplicate("students", column, value):
            raise HTTPException(
                status_code=400,
                detail=f"{label} already registered."
            )

        if check_duplicate("pending_registrations", column, value):
            raise HTTPException(
                status_code=400,
                detail="Registration is already waiting for Warden approval."
            )

        if check_duplicate("student_registration_otps", column, value):
            raise HTTPException(
                status_code=400,
                detail="Registration already awaiting OTP. Please resend OTP."
            )

    try:
        face_embedding = generate_face_embedding(image_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    email_otp = generate_email_otp()
    otp_expiry = generate_otp_expiry()

    data = {
        "roll_no": student.roll_no,
        "name": student.name,
        "email": student.email,
        "phone_number": student.phone_number,
        "hostel": student.hostel,
        "room_no": student.room_no,
        "branch": student.branch,
        "year": student.year,
        "password_hash": hash_pass(student.password),
        "face_embedding": face_embedding,
        "email_otp": email_otp,
        "otp_expiry": otp_expiry
    }

    try:
        supabase.table("student_registration_otps").insert(data).execute()

        send_email_otp(student.email, email_otp)

    except Exception:
        supabase.table("student_registration_otps").delete().eq(
            "email", student.email
        ).execute()

        raise HTTPException(
            status_code=500,
            detail="Registration or OTP email failed. Please try again."
        )

    return {
        "message": "Registration submitted. Please verify your email using the OTP sent to your inbox.",
        "email": student.email
    }


# =========================================================
# STUDENT OTP VERIFICATION
# =========================================================

def verify_email_otp(email, otp):

    response = (
        supabase.table("student_registration_otps")
        .select("*")
        .eq("email", email)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="No OTP registration found. Please register again."
        )

    registration = response.data[0]

    if registration["email_otp"] != otp:
        raise HTTPException(
            status_code=400,
            detail="Invalid OTP."
        )

    if is_otp_expired(registration["otp_expiry"]):
        raise HTTPException(
            status_code=400,
            detail="OTP has expired. Please request a new OTP."
        )

    student_data = {
        "roll_no": registration["roll_no"],
        "name": registration["name"],
        "email": registration["email"],
        "phone_number": registration["phone_number"],
        "hostel": registration["hostel"],
        "room_no": registration["room_no"],
        "branch": registration["branch"],
        "year": registration["year"],
        "password_hash": registration["password_hash"],
        "face_embedding": registration["face_embedding"],
        "email_verified": True
    }

    try:
        supabase.table("pending_registrations").insert(
            student_data
        ).execute()

        supabase.table("student_registration_otps").delete().eq(
            "email", email
        ).execute()

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Email verified, but registration could not be moved to Warden approval. Please contact the administrator."
        )

    return {
        "message": "Email verified successfully. Your registration is now waiting for Warden approval.",
        "student": {
            "roll_no": registration["roll_no"],
            "name": registration["name"],
            "email": registration["email"]
        }
    }


# =========================================================
# RESEND STUDENT OTP
# =========================================================

def resend_student_email_otp(email: str):

    response = (
        supabase.table("student_registration_otps")
        .select("email")
        .eq("email", email)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="No OTP registration found. Please register again."
        )

    email_otp = generate_email_otp()
    otp_expiry = generate_otp_expiry()

    supabase.table("student_registration_otps").update({
        "email_otp": email_otp,
        "otp_expiry": otp_expiry
    }).eq("email", email).execute()

    send_email_otp(email, email_otp)

    return {
        "message": "A new OTP has been sent to your email."
    }


# =========================================================
# WARDEN - PENDING STUDENT REGISTRATIONS
# =========================================================

def get_pending_student_registrations():

    response = (
        supabase.table("pending_registrations")
        .select(
            "id, roll_no, name, email, phone_number, hostel, room_no, branch, year, email_verified, created_at"
        )
        .eq("email_verified", True)
        .order("created_at", desc=True)
        .execute()
    )

    return response.data


# =========================================================
# WARDEN - APPROVE STUDENT REGISTRATION
# =========================================================

def approve_student_registration(roll_no: str, warden_id: int):

    response = (
        supabase.table("pending_registrations")
        .select(
            "roll_no, name, email, phone_number, hostel, room_no, branch, year, password_hash, face_embedding, email_verified"
        )
        .eq("roll_no", roll_no)
        .eq("email_verified", True)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="Verified pending student registration not found."
        )

    registration = response.data[0]

    student_data = {
        "roll_no": registration["roll_no"],
        "name": registration["name"],
        "email": registration["email"],
        "phone_number": registration["phone_number"],
        "hostel": registration["hostel"],
        "room_no": registration["room_no"],
        "branch": registration["branch"],
        "year": registration["year"],
        "password_hash": registration["password_hash"],
        "face_embedding": registration["face_embedding"]
    }

    try:
        supabase.table("students").insert(student_data).execute()

        supabase.table("pending_registrations").delete().eq(
            "roll_no", roll_no
        ).execute()

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Could not complete student approval. Please check the database."
        )

    return {
        "message": "Student registration approved successfully.",
        "student": {
            "roll_no": registration["roll_no"],
            "name": registration["name"],
            "email": registration["email"]
        }
    }


# =========================================================
# STUDENT FACE LOGIN
# =========================================================

def login_student_with_face(image_bytes: bytes):

    try:
        current_embedding = generate_face_embedding(image_bytes)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    response = (
        supabase.table("students")
        .select("roll_no, email, face_embedding")
        .not_.is_("face_embedding", "null")
        .execute()
    )

    students = response.data

    if not students:
        return {
            "message": "No registered student faces found",
            "face_login": False,
            "password_login_available": True
        }

    for student in students:

        stored_embedding = student["face_embedding"]

        if not stored_embedding:
            continue

        stored_embedding = np.array(
            stored_embedding,
            dtype=np.float64
        )

        current_embedding_array = np.array(
            current_embedding,
            dtype=np.float64
        )

        match = face_recognition.compare_faces(
            [stored_embedding],
            current_embedding_array,
            tolerance=0.5
        )

        if match[0]:

            access_token = create_access_token({
                "sub": student["roll_no"],
                "email": student["email"],
                "role": "student"
            })

            return {
                "message": "Face login successful",
                "face_login": True,
                "access_token": access_token,
                "token_type": "bearer"
            }

    return {
        "message": "Face not recognized",
        "face_login": False,
        "password_login_available": True
    }


# =========================================================
# STUDENT PASSWORD LOGIN
# =========================================================

def login_student_with_password(email, password):

    response = (
        supabase.table("students")
        .select("*")
        .eq("email", email)
        .execute()
    )

    students = response.data

    if not students:
        return {
            "error": "Invalid email or password"
        }

    student = students[0]

    if not verify_pass(password, student["password_hash"]):
        return {
            "error": "Invalid email or password"
        }

    access_token = create_access_token({
        "sub": student["roll_no"],
        "email": student["email"],
        "role": "student"
    })

    return {
        "message": "Password login successful",
        "access_token": access_token,
        "token_type": "bearer"
    }


# =========================================================
# STUDENT PROFILE
# =========================================================

def get_student_profile(roll_no: str):

    response = (
        supabase.table("students")
        .select("roll_no,name,email,hostel,room_no,branch,year")
        .eq("roll_no", roll_no)
        .execute()
    )

    if not response.data:
        return {"error": "Student not found"}

    return response.data[0]


# =========================================================
# COMPLAINT FUNCTIONS
# =========================================================

def create_complaint(roll_no: str, complaint):

    data = {
        "roll_no": roll_no,
        "category": complaint.category,
        "description": complaint.description
    }

    response = (
        supabase.table("complaints")
        .insert(data)
        .execute()
    )

    return response.data


def get_my_complaints(roll_no: str):

    response = (
        supabase.table("complaints")
        .select("*")
        .eq("roll_no", roll_no)
        .execute()
    )

    return response.data


def get_all_complaints():

    response = (
        supabase.table("complaints")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return response.data


def update_complaint_status(
    complaint_id: int,
    status: str,
    response_text: str | None,
    warden_id: int
):

    allowed_statuses = [
        "Pending",
        "In Progress",
        "Resolved",
        "Rejected"
    ]

    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid complaint status"
        )

    update_data = {
        "status": status,
        "response": response_text
    }

    if status == "Resolved":
        update_data["resolved_by"] = warden_id
        update_data["resolved_at"] = datetime.now(
            timezone.utc
        ).isoformat()

    result = (
        supabase.table("complaints")
        .update(update_data)
        .eq("id", complaint_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    return result.data[0]


# =========================================================
# STUDENT EXIT REQUEST
# =========================================================

def create_exit_request(roll_no: str, request):

    data = {
        "roll_no": roll_no,
        "destination": request.destination,
        "purpose": request.purpose,
        "expected_return": request.expected_return.isoformat(),
        "approval_status": "Pending"
    }

    response = (
        supabase.table("exit_requests")
        .insert(data)
        .execute()
    )

    return response.data


# =========================================================
# WARDEN REGISTRATION
# =========================================================

def register_warden(warden):

    if check_duplicate("wardens", "email", warden.email):
        raise HTTPException(
            status_code=400,
            detail="Email already registered."
        )

    hashed_password = hash_pass(warden.password)
    email_otp = generate_email_otp()
    otp_expiry = generate_otp_expiry()

    data = {
        "name": warden.name,
        "email": warden.email,
        "password_hash": hashed_password,
        "email_verified": False,
        "email_otp": email_otp,
        "otp_expiry": otp_expiry
    }

    supabase.table("wardens").insert(data).execute()

    send_email_otp(warden.email, email_otp)

    return {
        "message": "OTP sent to your email. Please verify your email."
    }


def resend_warden_email_otp(email: str):

    response = (
        supabase.table("wardens")
        .select("email, email_verified")
        .eq("email", email)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="Warden not found"
        )

    warden = response.data[0]

    if warden["email_verified"]:
        raise HTTPException(
            status_code=400,
            detail="Email is already verified"
        )

    email_otp = generate_email_otp()
    otp_expiry = generate_otp_expiry()

    supabase.table("wardens").update({
        "email_otp": email_otp,
        "otp_expiry": otp_expiry
    }).eq("email", email).execute()

    send_email_otp(email, email_otp)

    return {
        "message": "A new OTP has been sent to your email."
    }


def verify_warden_email_otp(email, otp):

    response = (
        supabase.table("wardens")
        .select("email, email_verified, email_otp, otp_expiry")
        .eq("email", email)
        .execute()
    )

    wardens = response.data

    if not wardens:
        return {
            "error": "No pending registration found."
        }

    warden = wardens[0]

    if warden["email_verified"]:
        return {
            "error": "Email is already verified."
        }

    if is_otp_expired(warden["otp_expiry"]):
        return {
            "error": "OTP has expired. Please register again."
        }

    if warden["email_otp"] != otp:
        return {
            "error": "Invalid OTP."
        }

    supabase.table("wardens").update({
        "email_verified": True,
        "email_otp": None,
        "otp_expiry": None
    }).eq("email", email).execute()

    return {
        "message": "Email verified successfully. Warden registration completed."
    }


# =========================================================
# WARDEN LOGIN
# =========================================================

def login_warden(email, password):

    response = (
        supabase.table("wardens")
        .select("warden_id, email, password_hash, email_verified")
        .eq("email", email)
        .execute()
    )

    wardens = response.data

    if not wardens:
        return {"error": "Invalid email or password"}

    warden = wardens[0]

    if not warden["email_verified"]:
        return {"error": "Please verify your email first"}

    if not verify_pass(password, warden["password_hash"]):
        return {"error": "Invalid email or password"}

    access_token = create_access_token({
        "sub": str(warden["warden_id"]),
        "email": warden["email"],
        "role": "warden"
    })

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer"
    }


# =========================================================
# WARDEN EXIT REQUESTS
# =========================================================

def get_pending_student_requests():

    response = (
        supabase.table("exit_requests")
        .select("*")
        .eq("approval_status", "Pending")
        .execute()
    )

    return response.data


def approve_student_request(request_id: int, warden_id: int):

    response = (
        supabase.table("exit_requests")
        .update({
            "approval_status": "Approved",
            "approved_by": warden_id,
            "approval_time": datetime.now(timezone.utc).isoformat(),
            "current_status": "Inside"
        })
        .eq("request_id", request_id)
        .eq("approval_status", "Pending")
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="Request not found or already processed"
        )

    return response.data[0]


def reject_student_request(
    request_id: int,
    warden_id: int,
    rejection_reason: str
):

    response = (
        supabase.table("exit_requests")
        .update({
            "approval_status": "Rejected",
            "approved_by": warden_id,
            "approval_time": datetime.now(timezone.utc).isoformat(),
            "rejection_reason": rejection_reason,
            "current_status": "Inside"
        })
        .eq("request_id", request_id)
        .eq("approval_status", "Pending")
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="Request not found or already processed"
        )

    return response.data[0]


# =========================================================
# GUARD REGISTRATION AND APPROVAL
# =========================================================

def register_guard(guard):

    password_hash = hash_pass(guard.password)

    data = {
        "name": guard.name,
        "email": guard.email,
        "password_hash": password_hash,
        "is_verified": False
    }

    supabase.table("guards").insert(data).execute()

    return {
        "message": "Guard registration successful. Awaiting warden approval."
    }


def get_pending_guards():

    response = (
        supabase.table("guards")
        .select("guard_id, name, email, is_verified, approved_by")
        .eq("is_verified", False)
        .execute()
    )

    return response.data


def approve_guard(guard_id: int, warden_id: int):

    response = (
        supabase.table("guards")
        .update({
            "is_verified": True,
            "approved_by": warden_id
        })
        .eq("guard_id", guard_id)
        .eq("is_verified", False)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="Guard not found or already approved"
        )

    guard = response.data[0]

    return {
        "message": "Guard approved successfully.",
        "guard": {
            "guard_id": guard["guard_id"],
            "name": guard["name"],
            "email": guard["email"],
            "is_verified": guard["is_verified"],
            "approved_by": guard["approved_by"]
        }
    }


# =========================================================
# GUARD LOGIN
# =========================================================

def login_guard(email, password):

    response = (
        supabase.table("guards")
        .select("guard_id, name, email, password_hash, is_verified")
        .eq("email", email)
        .execute()
    )

    guards = response.data

    if not guards:
        return {"error": "Invalid email or password"}

    guard = guards[0]

    if not guard["is_verified"]:
        return {"error": "Your account has not been approved by a warden"}

    if not verify_pass(password, guard["password_hash"]):
        return {"error": "Invalid email or password"}

    access_token = create_access_token({
        "sub": str(guard["guard_id"]),
        "email": guard["email"],
        "role": "guard"
    })

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer"
    }


# =========================================================
# GUARD EXIT AND RETURN
# =========================================================

def get_guard_approved_requests():

    response = (
        supabase.table("exit_requests")
        .select("*")
        .eq("approval_status", "Approved")
        .eq("current_status", "Inside")
        .execute()
    )

    return response.data


def guard_mark_exit(request_id: int, guard_id: int):

    receipt_number = (
        f"EXIT-{datetime.now(timezone.utc).year}-{request_id:06d}"
    )

    response = (
        supabase.table("exit_requests")
        .update({
            "exit_time": datetime.now(timezone.utc).isoformat(),
            "current_status": "Outside",
            "receipt_number": receipt_number
        })
        .eq("request_id", request_id)
        .eq("approval_status", "Approved")
        .eq("current_status", "Inside")
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="Approved request not found or student has already exited"
        )

    return response.data[0]


def guard_mark_return(request_id: int, guard_id: int, receipt_number: str):

    request = (
        supabase.table("exit_requests")
        .select("request_id, receipt_number, current_status, approval_status")
        .eq("request_id", request_id)
        .eq("receipt_number", receipt_number)
        .eq("approval_status", "Approved")
        .eq("current_status", "Outside")
        .execute()
    )

    if not request.data:
        raise HTTPException(
            status_code=404,
            detail="Invalid receipt number or student is not currently outside"
        )

    response = (
        supabase.table("exit_requests")
        .update({
            "return_time": datetime.now(timezone.utc).isoformat(),
            "return_guard": guard_id,
            "current_status": "Returned"
        })
        .eq("request_id", request_id)
        .eq("receipt_number", receipt_number)
        .eq("current_status", "Outside")
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="Return could not be recorded"
        )

    return {
        "message": "Student return verified successfully",
        "request_id": request_id,
        "current_status": "Returned"
    }


# =========================================================
# STUDENT EXIT REQUEST HISTORY
# =========================================================

def get_my_exit_requests(roll_no: str):

    response = (
        supabase.table("exit_requests")
        .select("*")
        .eq("roll_no", roll_no)
        .order("request_time", desc=True)
        .execute()
    )

    return response.data


def cancel_exit_request(request_id: int, roll_no: str):

    response = (
        supabase.table("exit_requests")
        .delete()
        .eq("request_id", request_id)
        .eq("roll_no", roll_no)
        .eq("approval_status", "Pending")
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="Pending exit request not found or cannot be cancelled"
        )

    return {
        "message": "Exit request cancelled and deleted successfully",
        "request_id": request_id
    }


# =========================================================
# WARDEN APPROVED / REJECTED REQUESTS
# =========================================================

def get_approved_student_requests():

    response = (
        supabase.table("exit_requests")
        .select("*")
        .eq("approval_status", "Approved")
        .execute()
    )

    return response.data


def get_rejected_student_requests():

    response = (
        supabase.table("exit_requests")
        .select("*")
        .eq("approval_status", "Rejected")
        .execute()
    )

    return response.data


def get_students_currently_outside():

    response = (
        supabase.table("exit_requests")
        .select("*")
        .eq("approval_status", "Approved")
        .eq("current_status", "Outside")
        .execute()
    )

    return response.data


def get_approved_guards():

    response = (
        supabase.table("guards")
        .select("guard_id, name, email, is_verified, approved_by")
        .eq("is_verified", True)
        .execute()
    )

    return response.data


# =========================================================
# DAILY ACTIVITY
# =========================================================

def get_today_exits():

    today = datetime.now(timezone.utc).date().isoformat()

    response = (
        supabase.table("exit_requests")
        .select("*")
        .gte("exit_time", f"{today}T00:00:00+00:00")
        .lt("exit_time", f"{today}T23:59:59+00:00")
        .order("exit_time", desc=True)
        .execute()
    )

    return response.data


def get_today_returns():

    today = datetime.now(timezone.utc).date().isoformat()

    response = (
        supabase.table("exit_requests")
        .select("*")
        .gte("return_time", f"{today}T00:00:00+00:00")
        .lt("return_time", f"{today}T23:59:59+00:00")
        .order("return_time", desc=True)
        .execute()
    )

    return response.data