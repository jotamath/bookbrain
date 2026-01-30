from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    #Relationships
    books = relationship("UserBook", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"

class UserBook(Base):
    __tablename__ = "user_books"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(String(100), nullable=False)  # Google Books ID
    title = Column(String(500), nullable=False)
    authors = Column(Text)  # Comma-separated
    description = Column(Text)
    categories = Column(Text)  # Comma-separated
    thumbnail = Column(String(500))
    google_rating = Column(Float, default=0.0)
    user_rating = Column(Integer)  # 1-5 stars
    status = Column(String(20), default="want_to_read")  # want_to_read, reading, finished
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="books")
    
    def __repr__(self):
        return f"<UserBook {self.title}>"