from backend.database import supabase
from backend.auth import hash_pass,verify_pass,create_access_token
from backend.services.otp_services import generate_email_otp,generate_otp_expiry,is_otp_expired
from backend.services.email_services import send_email_otp
from fastapi import HTTPException
from datetime import datetime,timezone
import face_recognition
from backend.face_utils import generate_face_embedding

def get_all_students():
    response = supabase.table("students").select("*").execute()
    return response.data

def check_duplicate(table, column, value):
    response = (
        supabase
        .table(table)
        .select(column)
        .eq(column, value)
        .execute()
    )

    return len(response.data) > 0


def create_pending_registration(student, image_bytes: bytes):

    # 1. Check duplicate roll number
    if check_duplicate("students", "roll_no", student.roll_no):
        raise HTTPException(
            status_code=400,
            detail="Roll number already registered."
        )

    if check_duplicate("pending_registrations", "roll_no", student.roll_no):
        raise HTTPException(
            status_code=400,
            detail="Registration already pending for this roll number."
        )

    # 2. Check duplicate email
    if check_duplicate("students", "email", student.email):
        raise HTTPException(
            status_code=400,
            detail="Email already registered."
        )

    if check_duplicate("pending_registrations", "email", student.email):
        raise HTTPException(
            status_code=400,
            detail="Registration already pending for this email."
        )

    # 3. Check duplicate phone
    if check_duplicate("students", "phone_number", student.phone_number):
        raise HTTPException(
            status_code=400,
            detail="Phone number already registered."
        )

    if check_duplicate("pending_registrations", "phone_number", student.phone_number):
        raise HTTPException(
            status_code=400,
            detail="Registration already pending for this phone number."
        )

    # 4. Generate face embedding
    try:
        face_embedding = generate_face_embedding(image_bytes)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    # 5. Hash password
    hashed_password = hash_pass(student.password)

    # 6. Generate OTP
    email_otp = generate_email_otp()
    otp_expiry = generate_otp_expiry()

    # 7. Prepare registration data
    data = {
        "roll_no": student.roll_no,
        "name": student.name,
        "email": student.email,
        "phone_number": student.phone_number,
        "hostel": student.hostel,
        "room_no": student.room_no,
        "branch": student.branch,
        "year": student.year,
        "password_hash": hashed_password,

        # Face embedding
        "face_embedding": face_embedding,

        # OTP
        "email_otp": email_otp,
        "otp_expiry": otp_expiry
    }

    # 8. Insert pending registration
    response = (
        supabase
        .table("pending_registrations")
        .insert(data)
        .execute()
    )

    # 9. Send OTP
    send_email_otp(
        student.email,
        email_otp
    )

    return response.data

def verify_email_otp(email, otp):

    # 1. Find pending registration
    response = (
        supabase
        .table("pending_registrations")
        .select("*")
        .eq("email", email)
        .execute()
    )

    registrations = response.data

    # 2. Check registration exists
    if not registrations:
        return {
            "error": "No pending registration found"
        }

    registration = registrations[0]

    # 3. Check email verification
    if registration["email_verified"]:
        return {
            "error": "Email is already verified"
        }

    # 4. Check OTP
    if registration["email_otp"] != otp:
        return {
            "error": "Invalid OTP"
        }

    # 5. Check OTP expiry
    if is_otp_expired(registration["otp_expiry"]):
        return {
            "error": "OTP has expired"
        }

    # 6. Mark email verified
    (
        supabase
        .table("pending_registrations")
        .update({
            "email_verified": True
        })
        .eq("email", email)
        .execute()
    )

    # 7. Prepare student data
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

        # Move face embedding to students table
        "face_embedding": registration["face_embedding"]
    }

    # 8. Insert into students table
    student_response = (
        supabase
        .table("students")
        .insert(student_data)
        .execute()
    )

    # 9. Delete pending registration
    (
        supabase
        .table("pending_registrations")
        .delete()
        .eq("email", email)
        .execute()
    )

    # 10. Return success
    return {
        "message": "Email verified and registration completed successfully",
        "student": student_response.data
    }
    
def login_student_with_face(image_bytes: bytes):

    # 1. Generate embedding from login image
    try:
        current_embedding = generate_face_embedding(image_bytes)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    # 2. Get registered student faces
    response = (
        supabase
        .table("students")
        .select("roll_no, email, face_embedding")
        .not_.is_("face_embedding", "null")
        .execute()
    )

    students = response.data

    # 3. No registered faces
    if not students:
        return {
            "message": "No registered student faces found",
            "face_login": False,
            "password_login_available": True
        }

    # 4. Compare face with registered students
    for student in students:

        stored_embedding = student["face_embedding"]

        if not stored_embedding:
            continue

        stored_embedding = [
            float(value)
            for value in stored_embedding
        ]

        match = face_recognition.compare_faces(
            [stored_embedding],
            current_embedding,
            tolerance=0.5
        )

        # 5. Face matched
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

    # 6. Face didn't match
    return {
        "message": "Face not recognized",
        "face_login": False,
        "password_login_available": True
    }
    
def login_student_with_password(email, password):

    response = (
        supabase
        .table("students")
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

    # Check password
    if not verify_pass(
        password,
        student["password_hash"]
    ):
        return {
            "error": "Invalid email or password"
        }

    # Create JWT
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
    
    


def get_student_profile(roll_no: str):
    response = (
        supabase
        .table("students")
        .select("roll_no,name,email,phone_number,hostel,room_no,branch,year")
        .eq("roll_no", roll_no)
        .execute()
    )

    if not response.data:
        return {"error": "Student not found"}

    return response.data[0]

def create_complaint(roll_no: str, complaint):
    data = {
        "roll_no": roll_no,
        "category": complaint.category,
        "description": complaint.description
    }

    response = (
        supabase
        .table("complaints")
        .insert(data)
        .execute()
    )

    return response.data

def get_my_complaints(roll_no: str):
    response = (
        supabase
        .table("complaints")
        .select("*")
        .eq("roll_no", roll_no)
        .execute()
    )

    return response.data

def get_all_complaints():
    response = (
        supabase
        .table("complaints")
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
        supabase
        .table("complaints")
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

def create_exit_request(roll_no: str, request):
    data = {
        "roll_no": roll_no,
        "destination": request.destination,
        "purpose": request.purpose,
        "expected_return": request.expected_return.isoformat(),
        "approval_status": "Pending"
    }

    response = (
        supabase
        .table("exit_requests")
        .insert(data)
        .execute()
    )

    return response.data

def register_warden(warden):

    # Check duplicate warden ID
    if check_duplicate("wardens", "warden_id", warden.warden_id):
        raise HTTPException(
            status_code=400,
            detail="Warden ID already registered."
        )

    # Check duplicate email
    if check_duplicate("wardens", "email", warden.email):
        raise HTTPException(
            status_code=400,
            detail="Email already registered."
        )

    # Hash password
    hashed_password = hash_pass(warden.password)

    # Generate OTP
    email_otp = generate_email_otp()

    # Generate OTP expiry
    otp_expiry = generate_otp_expiry()

    # Create unverified warden
    data = {
        "warden_id": warden.warden_id,
        "name": warden.name,
        "email": warden.email,
        "password_hash": hashed_password,
        "email_verified": False,
        "email_otp": email_otp,
        "otp_expiry": otp_expiry
    }

    # Store warden in database
    response = (
        supabase
        .table("wardens")
        .insert(data)
        .execute()
    )

    # Send OTP to email
    send_email_otp(
        warden.email,
        email_otp
    )

    # Don't return database data
    return {
        "message": "OTP sent to your email. Please verify your email."
    }
    
    
def verify_warden_email_otp(email, otp):

    # Find warden
    response = (
        supabase
        .table("wardens")
        .select("*")
        .eq("email", email)
        .execute()
    )

    wardens = response.data

    # No warden found
    if not wardens:
        return {
            "error": "No pending registration found."
        }

    warden = wardens[0]

    # Already verified
    if warden["email_verified"]:
        return {
            "error": "Email is already verified."
        }

    # Get expiry
    expiry = warden["otp_expiry"]

    # Supabase may return timezone information.
    # Convert it back to the format expected by your existing
    # is_otp_expired() function.
    if isinstance(expiry, str):
        expiry = expiry.replace("Z", "").split("+")[0]

    # Check whether OTP has expired
    # IMPORTANT: Do NOT delete here.
    # Database cleanup will delete expired unverified records.
    if is_otp_expired(expiry):
        return {
            "error": "OTP has expired. Please register again."
        }

    # Check OTP
    if warden["email_otp"] != otp:
        return {
            "error": "Invalid OTP."
        }

    # OTP is correct and still valid
    # Verify the warden
    (
        supabase
        .table("wardens")
        .update({
            "email_verified": True,
            "email_otp": None,
            "otp_expiry": None
        })
        .eq("email", email)
        .execute()
    )

    return {
        "message": "Email verified successfully. Warden registration completed."
    }
    
def login_warden(email, password):

    response = (
        supabase
        .table("wardens")
        .select("*")
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
    

def get_pending_student_requests():
    response = (
        supabase
        .table("exit_requests")
        .select("*")
        .eq("approval_status", "Pending")
        .execute()
    )

    return response.data


def approve_student_request(request_id: int, warden_id: int):

    response = (
        supabase
        .table("exit_requests")
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
        supabase
        .table("exit_requests")
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

def register_guard(guard):

    password_hash = hash_pass(guard.password)

    data = {
        "name": guard.name,
        "email": guard.email,
        "password_hash": password_hash,
        "is_verified": False
    }

    response = (
        supabase
        .table("guards")
        .insert(data)
        .execute()
    )

    return response.data

def get_pending_guards():
    response = (
        supabase
        .table("guards")
        .select("guard_id, name, email, is_verified, approved_by")
        .eq("is_verified", False)
        .execute()
    )

    return response.data

def approve_guard(guard_id: int, warden_id: int):

    response = (
        supabase
        .table("guards")
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

    return response.data[0]

def login_guard(email, password):

    response = (
        supabase
        .table("guards")
        .select("*")
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
    
def get_guard_approved_requests():
    response = (
        supabase
        .table("exit_requests")
        .select("*")
        .eq("approval_status", "Approved")
        .eq("current_status", "Inside")
        .execute()
    )

    return response.data


def guard_mark_exit(request_id: int, guard_id: int):
    response = (
        supabase
        .table("exit_requests")
        .update({
            "exit_time": datetime.now(timezone.utc).isoformat(),
            "current_status": "Outside"
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


def guard_mark_return(request_id: int, guard_id: int):
    response = (
        supabase
        .table("exit_requests")
        .update({
            "return_time": datetime.now(timezone.utc).isoformat(),
            "return_guard": guard_id,
            "current_status": "Returned"
        })
        .eq("request_id", request_id)
        .eq("approval_status", "Approved")
        .eq("current_status", "Outside")
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="Request not found or student has not exited"
        )

    return response.data[0]

def get_my_exit_requests(roll_no: str):
    response = (
        supabase
        .table("exit_requests")
        .select("*")
        .eq("roll_no", roll_no)
        .order("request_time", desc=True)
        .execute()
    )

    return response.data


def cancel_exit_request(request_id: int, roll_no: str):
    response = (
        supabase
        .table("exit_requests")
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
    
def get_approved_student_requests():
    response = (
        supabase
        .table("exit_requests")
        .select("*")
        .eq("approval_status", "Approved")
        .execute()
    )

    return response.data


def get_rejected_student_requests():
    response = (
        supabase
        .table("exit_requests")
        .select("*")
        .eq("approval_status", "Rejected")
        .execute()
    )

    return response.data


def get_students_currently_outside():
    response = (
        supabase
        .table("exit_requests")
        .select("*")
        .eq("approval_status", "Approved")
        .eq("current_status", "Outside")
        .execute()
    )

    return response.data


def get_approved_guards():
    response = (
        supabase
        .table("guards")
        .select(
            "guard_id, name, email, is_verified, approved_by"
        )
        .eq("is_verified", True)
        .execute()
    )

    return response.data

def get_today_exits():
    today = datetime.now(timezone.utc).date().isoformat()

    response = (
        supabase
        .table("exit_requests")
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
        supabase
        .table("exit_requests")
        .select("*")
        .gte("return_time", f"{today}T00:00:00+00:00")
        .lt("return_time", f"{today}T23:59:59+00:00")
        .order("return_time", desc=True)
        .execute()
    )

    return response.data
