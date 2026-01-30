from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import settings

#Database URL
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

#Criar engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)

#Session local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#Base para modelos
Base = declarative_base()

#Dependency para obter sessão no banco 
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()