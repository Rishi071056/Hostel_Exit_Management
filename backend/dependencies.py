from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.auth import verify_access_token


security = HTTPBearer()


def get_current_student(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    payload = verify_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return payload




security = HTTPBearer()


def get_current_warden(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    payload = verify_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    if payload.get("role") != "warden":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Warden access required"
        )

    return payload

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.auth import verify_access_token

security = HTTPBearer()


def get_current_guard(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    payload = verify_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    if payload.get("role") != "guard":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Guard access required"
        )

    return payload
