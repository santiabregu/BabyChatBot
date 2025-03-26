from sqlalchemy import Column, Integer, String, Date, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Define the database URL
DATABASE_URL = "sqlite:///./babychatbot.db"

# Create the database engine
engine = create_engine(DATABASE_URL)

# Define the base class for models
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)

class UserFormData(Base):
    __tablename__ = "user_form_data"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)  # Link to the logged-in user
    due_date = Column(Date, nullable=False)
    baby_gender = Column(String, nullable=False)
    user_name = Column(String, nullable=False)