from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.status import HTTP_401_UNAUTHORIZED
from sqlalchemy.orm import Session
from typing import Optional
import time

import security
from database import get_db, User

security_scheme = HTTPBearer()

def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    token = credentials.credentials
    payload = security.verify_jwt(token)
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=401, detail="Sessão administrativa inválida ou expirada.")
    return payload

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme), db: Session = Depends(get_db)):
    token = credentials.credentials
    payload = security.verify_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token de sessão inválido ou expirado.")
    user_id = payload.get("user_id")
    role = payload.get("role")
    
    if role == "admin":
        return {"id": 0, "email": "admin@vagasync.com", "role": "admin", "name": "Super Admin"}
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuário associado ao token não encontrado.")
    return user

def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)), db: Session = Depends(get_db)):
    if not credentials:
        return None
    token = credentials.credentials
    payload = security.verify_jwt(token)
    if not payload:
        return None
    role = payload.get("role")
    user_id = payload.get("user_id")
    if role == "admin":
        return {"id": 0, "email": "admin@vagasync.com", "role": "admin", "name": "Super Admin"}
    return db.query(User).filter(User.id == user_id).first()

def get_user_from_token(token: str, db: Session):
    payload = security.verify_jwt(token)
    if not payload:
        return None
    user_id = payload.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()

# Config Bearer Dependency
_config_bearer = HTTPBearer(auto_error=False)

def _require_valid_token(credentials: HTTPAuthorizationCredentials = Depends(_config_bearer)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Token de autenticação obrigatório.")
    payload = security.verify_jwt(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")
    return payload
