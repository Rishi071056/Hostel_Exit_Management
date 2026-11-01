import bcrypt
from backend.config import JWT_ACCESS_TOKEN_EXPIRE_MINUTES,JWT_ALGORITHM,JWT_SECRET_KEY
from datetime import datetime,timedelta,timezone
from jose import jwt,JWTError

def hash_pass(password: str):
    return bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()

def verify_pass(password: str, hashed_password: str):
    return bcrypt.checkpw(
        password.encode(),
        hashed_password.encode()
    )
    
def create_access_token(data: dict):
    to_encode = data.copy()

    # JWT "sub" must always be a string
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({
        "exp": expire
    })

    return jwt.encode(
        to_encode,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )
    
def verify_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

        print("TOKEN PAYLOAD:", payload)

        return payload

    except JWTError as e:
        print("JWT ERROR:", repr(e))
        return None
    
