from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# URL do banco, exemplo para SQLite local (troque pelo seu banco, ex: PostgreSQL)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}  # só para SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
