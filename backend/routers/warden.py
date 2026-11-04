from fastapi import APIRouter, Depends, HTTPException

from backend.schemas import (
    ResendOTPRequest,
    WardenRegister,
    WardenEmailOTPVerification,
    WardenLogin,
    WardenRequestDecision,
    ComplaintStatusUpdate
)

from backend.crud import (
    register_warden,
    verify_warden_email_otp,
    login_warden,
    reject_student_request,
    approve_student_request,
    get_pending_student_requests,
    get_all_complaints,
    update_complaint_status,
    get_pending_guards,
    approve_guard,
    get_approved_student_requests,
    get_rejected_student_requests,
    get_students_currently_outside,
    get_approved_guards,
    resend_warden_email_otp,
    get_pending_student_registrations,
    approve_student_registration
)

from backend.dependencies import get_current_warden
from backend.database import supabase

router = APIRouter()


# WARDEN REGISTRATION

@router.post("/register")
def register(warden: WardenRegister):
    return register_warden(warden)


@router.post("/verify-email")
def verify_email(data: WardenEmailOTPVerification):
    return verify_warden_email_otp(data.email, data.otp)


@router.post("/resend-otp")
def resend_otp(data: ResendOTPRequest):
    return resend_warden_email_otp(data.email)


@router.post("/login")
def login(data: WardenLogin):
    return login_warden(data.email, data.password)


# WARDEN PROFILE

@router.get("/profile")
def get_warden_profile(
    current_warden=Depends(get_current_warden)
):
    warden_id = int(current_warden["sub"])

    response = (
        supabase.table("wardens")
        .select("warden_id, name, email, email_verified")
        .eq("warden_id", warden_id)
        .single()
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="Warden not found"
        )

    return {
        "message": "Warden profile",
        "warden": response.data
    }


# =====================================================
# STUDENT REGISTRATION APPROVAL
# =====================================================

@router.get("/registrations/pending")
def get_pending_registrations(
    current_warden=Depends(get_current_warden)
):
    return get_pending_student_registrations()


@router.post("/registrations/{roll_no}/approve")
def approve_registration(
    roll_no: str,
    current_warden=Depends(get_current_warden)
):
    warden_id = int(current_warden["sub"])

    return approve_student_registration(
        roll_no,
        warden_id
    )


# =====================================================
# EXIT REQUESTS
# =====================================================

@router.get("/requests/pending")
def get_pending_requests(
    current_warden=Depends(get_current_warden)
):
    return get_pending_student_requests()


@router.post("/requests/{request_id}/approve")
def approve_request(
    request_id: int,
    current_warden=Depends(get_current_warden)
):
    warden_id = int(current_warden["sub"])

    return approve_student_request(
        request_id,
        warden_id
    )


@router.post("/requests/{request_id}/reject")
def reject_request(
    request_id: int,
    data: WardenRequestDecision,
    current_warden=Depends(get_current_warden)
):
    if not data.rejection_reason:
        raise HTTPException(
            status_code=400,
            detail="Rejection reason is required"
        )

    warden_id = int(current_warden["sub"])

    return reject_student_request(
        request_id,
        warden_id,
        data.rejection_reason
    )


# =====================================================
# COMPLAINTS
# =====================================================

@router.get("/complaints")
def get_complaints(
    current_warden=Depends(get_current_warden)
):
    return get_all_complaints()


@router.put("/complaints/{complaint_id}")
def update_complaint(
    complaint_id: int,
    data: ComplaintStatusUpdate,
    current_warden=Depends(get_current_warden)
):
    warden_id = int(current_warden["sub"])

    return update_complaint_status(
        complaint_id,
        data.status,
        data.response,
        warden_id
    )


# =====================================================
# GUARD APPROVAL
# =====================================================

@router.get("/guards/pending")
def get_pending_guards_list(
    current_warden=Depends(get_current_warden)
):
    return get_pending_guards()


@router.post("/guards/{guard_id}/approve")
def approve_guard_request(
    guard_id: int,
    current_warden=Depends(get_current_warden)
):
    warden_id = int(current_warden["sub"])

    return approve_guard(
        guard_id,
        warden_id
    )


@router.get("/guards/approved")
def get_approved_guards_list(
    current_warden=Depends(get_current_warden)
):
    return get_approved_guards()


# =====================================================
# APPROVED AND REJECTED EXIT REQUESTS
# =====================================================

@router.get("/exit-requests/approved")
def get_approved_requests(
    current_warden=Depends(get_current_warden)
):
    return get_approved_student_requests()


@router.get("/exit-requests/rejected")
def get_rejected_requests(
    current_warden=Depends(get_current_warden)
):
    return get_rejected_student_requests()


# =====================================================
# STUDENTS CURRENTLY OUTSIDE
# =====================================================

@router.get("/students/outside")
def get_outside_students(
    current_warden=Depends(get_current_warden)
):
    return get_students_currently_outside()