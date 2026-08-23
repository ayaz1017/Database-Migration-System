from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import sqlite3
import uuid
from datetime import datetime

from backend.services.auth_service import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    get_current_user,
    require_admin,
    require_member_or_above,
    get_db,
    DB_FILE
)
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["auth"])

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "Viewer"

class UserResponse(BaseModel):
    id: str
    org_id: str
    email: EmailStr
    role: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class RefreshRequest(BaseModel):
    refresh_token: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate):
    clean_email = user.email.strip().lower()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE LOWER(email) = ?", (clean_email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")
    
    org_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    hashed_pw = get_password_hash(user.password)
    
    org_name = f"{clean_email.split('@')[0]}'s Org"
    cursor.execute("INSERT INTO organizations (id, name) VALUES (?, ?)", (org_id, org_name))
    cursor.execute(
        "INSERT INTO users (id, org_id, email, hashed_password, role) VALUES (?, ?, ?, ?, ?)",
        (user_id, org_id, clean_email, hashed_pw, "Admin")
    )
    conn.commit()
    
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    new_user = cursor.fetchone()
    conn.close()
    return dict(new_user)

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    clean_email = form_data.username.strip().lower()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (clean_email,))
    user = cursor.fetchone()
    conn.close()
    
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user["id"], "org_id": user["org_id"], "role": user["role"]})
    refresh_token = create_refresh_token(user["id"])
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/refresh", response_model=Token)
def refresh_token(req: RefreshRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM refresh_tokens WHERE token = ?", (req.refresh_token,))
    token_row = cursor.fetchone()
    
    if not token_row:
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid refresh token")
        
    if datetime.fromisoformat(token_row["expires_at"]) < datetime.utcnow():
        cursor.execute("DELETE FROM refresh_tokens WHERE token = ?", (req.refresh_token,))
        conn.commit()
        conn.close()
        raise HTTPException(status_code=401, detail="Refresh token expired")
        
    user_id = token_row["user_id"]
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    # Rotate refresh token
    cursor.execute("DELETE FROM refresh_tokens WHERE token = ?", (req.refresh_token,))
    conn.commit()
    conn.close()
    
    access_token = create_access_token(data={"sub": user["id"], "org_id": user["org_id"], "role": user["role"]})
    new_refresh = create_refresh_token(user["id"])
    return {"access_token": access_token, "refresh_token": new_refresh, "token_type": "bearer"}

@router.post("/logout")
def logout(req: RefreshRequest, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM refresh_tokens WHERE token = ? AND user_id = ?", (req.refresh_token, current_user["id"]))
    conn.commit()
    conn.close()
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    return dict(current_user)

@router.post("/change-password")
def change_password(req: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    if not verify_password(req.old_password, current_user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    
    hashed_pw = get_password_hash(req.new_password)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET hashed_password = ? WHERE id = ?", (hashed_pw, current_user["id"]))
    
    cursor.execute("DELETE FROM refresh_tokens WHERE user_id = ?", (current_user["id"],))
    conn.commit()
    conn.close()
    return {"message": "Password updated successfully"}

@router.post("/invite", response_model=UserResponse)
def invite_user(user: UserCreate, current_user: dict = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (user.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")
        
    user_id = str(uuid.uuid4())
    hashed_pw = get_password_hash(user.password) 
    
    cursor.execute(
        "INSERT INTO users (id, org_id, email, hashed_password, role) VALUES (?, ?, ?, ?, ?)",
        (user_id, current_user["org_id"], user.email, hashed_pw, user.role)
    )
    conn.commit()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    new_user = cursor.fetchone()
    conn.close()
    return dict(new_user)

@router.get("/users", response_model=List[UserResponse])
def list_users(current_user: dict = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE org_id = ?", (current_user["org_id"],))
    users = cursor.fetchall()
    conn.close()
    return [dict(u) for u in users]
