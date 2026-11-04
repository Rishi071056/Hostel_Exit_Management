from pydantic import BaseModel,model_validator,field_validator
import re
from datetime import datetime

class StudentRegister(BaseModel):
    roll_no: str
    name: str
    email: str
    hostel: str
    room_no: str
    branch: str
    year: int
    phone_number: str
    password: str

    # Roll Number Validation
    @field_validator("roll_no")
    @classmethod
    def validate_roll_no(cls, value):
        value = value.strip().upper()

        if not re.fullmatch(r"\d{2}[A-Z]{3}\d{3}", value):
            raise ValueError(
                "Roll number must be in format like 24BME115"
            )

        return value

    # Email Validation
    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        value = value.strip().lower()

        if not re.fullmatch(
            r"\d{2}[a-z]{3}\d{3}@nith\.ac\.in",
            value
        ):
            raise ValueError(
                "Email must be in format like 24bme115@nith.ac.in"
            )

        return value

    # Phone Number Validation
    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value):
        value = value.strip()

        if not re.fullmatch(r"[6-9]\d{9}", value):
            raise ValueError(
                "Phone number must be a valid 10-digit number"
            )

        return value

    # Roll Number and Email Prefix Validation
    @model_validator(mode="after")
    def validate_roll_email_match(self):

        roll_no = self.roll_no
        email_prefix = self.email.split("@")[0].upper()

        if roll_no != email_prefix:
            raise ValueError(
                "Roll number and email ID must match"
            )

        return self


class PendingRegistration(BaseModel):
    roll_no: str
    name: str
    email: str
    phone_number: str
    hostel: str
    room_no: str
    branch: str
    year: int
    password_hash: str

    # Face embedding
    face_embedding: list[float] | None = None

    email_otp: str | None = None
    otp_expiry: str | None = None


class EmailOTPVerification(BaseModel):
    email: str
    otp: str

class ResendOTPRequest(BaseModel):
    email: str    


class StudentLogin(BaseModel):
    email: str
    password: str


class ComplaintCreate(BaseModel):
    category: str
    description: str
    
class ComplaintStatusUpdate(BaseModel):
    status: str
    response:str |None=None
    
class ExitRequestCreate(BaseModel):
    destination: str
    purpose: str
    expected_return: datetime
    
class WardenRegister(BaseModel):
    
    name: str
    email: str
    password: str
    
class WardenLogin(BaseModel):
    email: str
    password: str
    
class GuardRegister(BaseModel):
    name: str
    email: str
    password: str
    
class GuardLogin(BaseModel):
    email: str
    password: str
    
class WardenEmailOTPVerification(BaseModel):
    email: str
    otp: str
    
class WardenRequestDecision(BaseModel):
    rejection_reason: str | None = None