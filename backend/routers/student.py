from fastapi import APIRouter,Depends,UploadFile,File,Form
from backend.schemas import StudentRegister,EmailOTPVerification,StudentLogin,ComplaintCreate,ExitRequestCreate
from backend.crud import (create_pending_registration,verify_email_otp,login_student_with_face,login_student_with_password,
                          get_student_profile,create_complaint,get_my_complaints,create_exit_request,
                          get_my_exit_requests,cancel_exit_request)
from backend.dependencies import get_current_student




router = APIRouter()

@router.post("/register")
async def register(
    roll_no: str = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    hostel: str = Form(...),
    room_no: str = Form(...),
    branch: str = Form(...),
    year: int = Form(...),
    phone_number: str = Form(...),
    password: str = Form(...),
    image: UploadFile = File(...)
):

    # Read uploaded face image
    image_bytes = await image.read()

    # Create and validate StudentRegister object
    student = StudentRegister(
        roll_no=roll_no,
        name=name,
        email=email,
        hostel=hostel,
        room_no=room_no,
        branch=branch,
        year=year,
        phone_number=phone_number,
        password=password
    )

    # Send student + image to CRUD
    return create_pending_registration(
        student,
        image_bytes
    )
    
@router.post("/login-face")
async def login_face(
    image: UploadFile = File(...)
):

    # Read face image
    image_bytes = await image.read()

    # Face-only authentication
    return login_student_with_face(
        image_bytes
    )
    
@router.post("/login-password")
def login_password(data: StudentLogin):

    return login_student_with_password(
        data.email,
        data.password
    )

@router.post("/verify-email")
def verify_email(data: EmailOTPVerification):
    return verify_email_otp(data.email,data.otp)

    
@router.get("/profile")
def get_profile(current_student = Depends(get_current_student)):
    roll_no=current_student["sub"]
    student=get_student_profile(roll_no)
    return {
        "message": "You are authenticated",
        "student": student
    }
    
@router.post("/complaints")
def create_student_complaint(
    complaint: ComplaintCreate,
    current_student = Depends(get_current_student)
):
    roll_no = current_student["sub"]

    return create_complaint(roll_no, complaint)


@router.get("/complaints")
def get_complaints(
    current_student = Depends(get_current_student)
):
    roll_no = current_student["sub"]

    return get_my_complaints(roll_no)

@router.post("/exit-requests")
def create_exit(
    request: ExitRequestCreate,
    current_student = Depends(get_current_student)
):
    roll_no = current_student["sub"]

    return create_exit_request(roll_no, request)

@router.get("/exit-requests")
def get_my_exit_requests_route(
    current_student=Depends(get_current_student)
):
    roll_no = current_student["sub"]

    return get_my_exit_requests(roll_no)

@router.delete("/exit-requests/{request_id}")
def cancel_student_exit_request(
    request_id: int,
    current_student=Depends(get_current_student)
):
    roll_no = current_student["sub"]

    return cancel_exit_request(
        request_id,
        roll_no
    )


    
