from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session

# Importe suas configs aqui (assumindo que o arquivo se chama config.py)
from .config import settings
from .database import get_db
from .models import User

# --- MUDANÇA 1: Configurações via Pydantic ---
# Não usamos mais os.getenv aqui. O Pydantic garante que se o app subiu,
# a SECRET_KEY existe.
# ALGORITHM e EXPIRE também vêm do settings para centralizar.

# --- MUDANÇA 2: Upgrade para Argon2 (Extremamente Seguro) ---
# Argon2id é resistente a GPU e não tem o limite de 72 caracteres do Bcrypt.
pwd_context = CryptContext(
    schemes=["argon2"], 
    deprecated="auto"
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar senha com Argon2"""
    try:
        # A lógica de truncar (>72) foi REMOVIDA. 
        # Argon2 lida nativamente com senhas longas.
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        # Em produção, use logging ao invés de print
        print(f"Erro ao verificar senha: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Gerar hash seguro com Argon2"""
    try:
        return pwd_context.hash(password)
    except Exception as e:
        print(f"Erro ao fazer hash da senha: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar segurança da senha")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Criar token JWT"""
    to_encode = data.copy()
    
    # Uso de timezone.utc é a prática moderna recomendada
    now = datetime.now(timezone.utc)
    
    if expires_delta:
        expire = now + expires_delta
    else:
        # Usando o valor do settings
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Usando chave e algoritmo do settings
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[str]:
    """Decodificar token JWT"""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        return username
    except JWTError:
        return None

# O restante das funções (get_current_user_from_cookie, require_auth)
# permanece igual, pois dependem apenas da lógica acima.
async def get_current_user_from_cookie(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    if token.startswith("Bearer "):
        token = token[7:]
    
    username = decode_token(token)
    if not username:
        return None
    
    user = db.query(User).filter(User.username == username).first()
    return user

async def require_auth(request: Request, db: Session = Depends(get_db)) -> User:
    user = await get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return user