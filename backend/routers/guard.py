from fastapi import APIRouter

from backend.schemas import GuardRegister, GuardLogin
from backend.crud import (register_guard, login_guard,
                          get_guard_approved_requests,guard_mark_exit,guard_mark_return,
                          get_students_currently_outside,get_today_exits,get_today_returns)
from fastapi import Depends,Body

from backend.dependencies import get_current_guard


router = APIRouter()


@router.post("/register")
def register(guard: GuardRegister):
    return register_guard(guard)

@router.post("/login")
def login(data: GuardLogin):
    return login_guard(
        data.email,
        data.password
    )
    
@router.get("/profile")
def get_guard_profile(
    current_guard=Depends(get_current_guard)
):
    return {
        "message": "Guard profile",
        "guard": {
            "guard_id": int(current_guard["sub"]),
            "email": current_guard["email"],
            "role": current_guard["role"]
        }
    }
    
@router.get("/requests/approved")
def get_approved_requests(
    current_guard=Depends(get_current_guard)
):
    return get_guard_approved_requests()

@router.post("/requests/{request_id}/exit")

def mark_student_exit(
    request_id: int,
    current_guard=Depends(get_current_guard)
):
    guard_id = int(current_guard["sub"])

    return guard_mark_exit(
        request_id,
        guard_id
    )
    
@router.post("/requests/{request_id}/return")
def mark_student_return(
    request_id: int,
    receipt_number: str = Body(..., embed=True),
    current_guard=Depends(get_current_guard)
):
    guard_id = int(current_guard["sub"])
    return guard_mark_return(request_id, guard_id, receipt_number)
    
@router.get("/students/outside")
def get_students_outside(
    current_guard=Depends(get_current_guard)
):
    return get_students_currently_outside()


@router.get("/exits/today")
def get_exits_today(
    current_guard=Depends(get_current_guard)
):
    return get_today_exits()


@router.get("/returns/today")
def get_returns_today(
    current_guard=Depends(get_current_guard)
):
    return get_today_returns()
    
    
