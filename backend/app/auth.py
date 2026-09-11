import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from .database import query_one, execute_insert
import json

security = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}:{key.hex()}"

def verify_password(stored_hash: str, provided_password: str) -> bool:
    try:
        salt, key_hex = stored_hash.split(":")
        new_key = hashlib.pbkdf2_hmac(
            'sha256',
            provided_password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return secrets.compare_digest(new_key.hex(), key_hex)
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    to_encode.update({"exp": expire, "iat": now})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(
    request: Request,
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    token = None
    if auth and auth.credentials:
        token = auth.credentials
    elif "authorization" in request.headers:
        auth_hdr = request.headers.get("authorization")
        if auth_hdr.lower().startswith("bearer "):
            token = auth_hdr.split(" ", 1)[1].strip()
        else:
            token = auth_hdr.strip()
    else:
        # Check cookie fallback
        token = request.cookies.get("careaura_token") or request.cookies.get("aegiscare_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_token(token)
    sub_val = payload.get("sub")
    if sub_val is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims.",
        )
    user_id = int(sub_val)
    
    user = query_one(
        "SELECT id, email, role, full_name, phone, avatar_url, is_active, created_at FROM users WHERE id = ?",
        (user_id,)
    )
    if not user or not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated or does not exist.",
        )
    
    # Attach role specific profile id
    if user["role"] == "patient":
        p = query_one("SELECT id, mrn FROM patients WHERE user_id = ?", (user["id"],))
        user["patient_id"] = p["id"] if p else None
        user["mrn"] = p["mrn"] if p else None
    elif user["role"] == "doctor":
        d = query_one("SELECT id, department_id, specialization FROM doctors WHERE user_id = ?", (user["id"],))
        user["doctor_id"] = d["id"] if d else None
        user["department_id"] = d["department_id"] if d else None
        user["specialization"] = d["specialization"] if d else None
    
    return user

def require_role(allowed_roles: List[str]):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker

require_patient = require_role(["patient"])
require_doctor = require_role(["doctor"])
require_admin = require_role(["admin"])
require_clinical_staff = require_role(["doctor", "admin"])

def log_audit(user_id: Optional[int], action: str, resource_type: str, resource_id: str = None, details: dict = None, ip: str = "127.0.0.1"):
    try:
        execute_insert(
            """INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details_json, ip_address, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                action,
                resource_type,
                str(resource_id) if resource_id is not None else None,
                json.dumps(details or {}),
                ip,
                datetime.now(timezone.utc).isoformat()
            )
        )
    except Exception as e:
        print(f"Audit log failed: {e}")
