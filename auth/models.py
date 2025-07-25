from pydantic import BaseModel

class User(BaseModel):
    username: str
    password: str  # Хранится только хеш!
    role: str      # "admin" или "user"

class Token(BaseModel):
    access_token: str
    token_type: str