import os
import time
import hmac
import hashlib
import struct
import base64
import json
from typing import Optional

JWT_SECRET = "vagasync_super_secret_jwt_key_2026"
ENCRYPTION_SECRET = "vagasyncsuperadminfinancialsecret2026"
TOTP_SECRET = "VAGASYNCSUPERADM" # base32 format (16 chars)

# --- 2FA / TOTP ---
def get_totp_token(secret: str, intervals_no: int) -> str:
    # pad secret to a multiple of 8 if needed
    secret = secret.strip()
    rem = len(secret) % 8
    if rem > 0:
        secret += "=" * (8 - rem)
    key = base64.b32decode(secret, casefold=True)
    msg = struct.pack(">Q", intervals_no)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    o = h[19] & 15
    token = (struct.unpack(">I", h[o:o+4])[0] & 0x7fffffff) % 1000000
    return "{:06d}".format(token)

def verify_totp(secret: str, code: str) -> bool:
    try:
        code = str(code).strip()
        if len(code) != 6:
            return False
        # Allow +/- 1 interval (30 seconds window)
        t = int(time.time() / 30)
        for i in range(-1, 2):
            if get_totp_token(secret, t + i) == code:
                return True
    except Exception:
        pass
    return False

# --- JWT TOKENS ---
def create_jwt(payload: dict, expires_in: int = 3600) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = payload.copy()
    payload["exp"] = int(time.time()) + expires_in
    
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().replace("=", "")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().replace("=", "")
    
    signature_base = f"{header_b64}.{payload_b64}"
    sig = hmac.new(JWT_SECRET.encode(), signature_base.encode(), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode().replace("=", "")
    
    return f"{signature_base}.{sig_b64}"

def verify_jwt(token: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        
        # Verify signature
        signature_base = f"{header_b64}.{payload_b64}"
        sig = hmac.new(JWT_SECRET.encode(), signature_base.encode(), hashlib.sha256).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(sig).decode().replace("=", "")
        
        if not hmac.compare_digest(sig_b64, expected_sig_b64):
            return None
            
        # Decode payload
        rem = len(payload_b64) % 4
        if rem > 0:
            payload_b64 += "=" * (4 - rem)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode()).decode())
        
        if payload.get("exp", 0) < time.time():
            return None
            
        return payload
    except Exception:
        return None

# --- SYMMETRIC ENCRYPTION FOR SENSITIVE DB CONFIGS ---
def encrypt_data(data: str) -> str:
    if not data:
        return ""
    key = hashlib.sha256(ENCRYPTION_SECRET.encode()).digest()
    data_bytes = data.encode('utf-8')
    encrypted = bytearray()
    for i in range(len(data_bytes)):
        k_byte = key[i % len(key)]
        encrypted.append(data_bytes[i] ^ k_byte)
    return base64.b64encode(encrypted).decode('utf-8')

def decrypt_data(encrypted_base64: str) -> str:
    if not encrypted_base64:
        return ""
    try:
        key = hashlib.sha256(ENCRYPTION_SECRET.encode()).digest()
        encrypted = base64.b64decode(encrypted_base64.encode('utf-8'))
        decrypted = bytearray()
        for i in range(len(encrypted)):
            k_byte = key[i % len(key)]
            decrypted.append(encrypted[i] ^ k_byte)
        return decrypted.decode('utf-8')
    except Exception:
        return ""
