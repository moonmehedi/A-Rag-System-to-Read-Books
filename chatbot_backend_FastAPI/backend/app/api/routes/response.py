from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.models.chat_message import ChatMessage
from passlib.context import CryptContext
import jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from pydantic import BaseModel
import uuid

SECRET_KEY = "supersecretkey"  # Use env var in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

router = APIRouter()

# Dependency

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# User schemas
class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: uuid.UUID
    username: str
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

# Auth utils

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.get("/")
async def default_response():
    return {"message": "This is a default response from the backend."}

@router.get("/test-response")
async def chapter_summary():
    return {
        "response": "Absolutely! Here's a detailed summary to help you understand the key concepts presented in the chapter. In this section, the author delves deep into the philosophical underpinnings of human motivation, drawing from both classical and modern sources. The discussion begins with an exploration of Maslow’s Hierarchy of Needs, outlining how human behavior is often driven by the pursuit of fundamental physiological needs before progressing to safety, love/belonging, esteem, and finally, self-actualization. This framework serves as a foundation for later arguments concerning societal structures and personal development. The author then transitions to a comparative analysis between Eastern and Western philosophical traditions, highlighting the ways in which Stoicism, Buddhism, and existentialism address the search for meaning and inner peace. Throughout the chapter, case studies and illustrative anecdotes are provided, allowing the reader to ground theoretical ideas in real-world applications. A recurring theme is the importance of self-awareness and conscious decision-making in shaping one’s life path. The language used is both accessible and profound, making complex ideas digestible without sacrificing intellectual depth. Overall, this chapter serves as a compelling argument for the integration of psychological and philosophical insights into daily living. If you would like a visual summary or a simplified version with bullet points and examples, just let me know!"
    }

# Register endpoint
@router.post("/auth/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    db_user = User(username=user.username, password_hash=get_password_hash(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Login endpoint
@router.post("/auth/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

# --- Chat Message Schemas ---
class ChatMessageCreate(BaseModel):
    content: str
    parent_id: uuid.UUID | None = None
    doc_id: str | None = None
    is_user: bool = True

class ChatMessageOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    parent_id: uuid.UUID | None
    ltree_path: str
    content: str
    is_user: bool
    timestamp: datetime
    doc_id: str | None
    class Config:
        orm_mode = True

# --- Chat Message Endpoints ---
from sqlalchemy import select

@router.post("/chat/message", response_model=ChatMessageOut)
def create_message(
    msg: ChatMessageCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Compute ltree_path
    if msg.parent_id:
        parent = db.query(ChatMessage).filter(ChatMessage.id == msg.parent_id, ChatMessage.user_id == user.id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent message not found")
        ltree_path = parent.ltree_path + f'.{uuid.uuid4().hex[:8]}'
    else:
        ltree_path = uuid.uuid4().hex[:8]
    db_msg = ChatMessage(
        user_id=user.id,
        parent_id=msg.parent_id,
        ltree_path=ltree_path,
        content=msg.content,
        is_user=msg.is_user,
        doc_id=msg.doc_id,
    )
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)
    return db_msg

@router.get("/chat/tree", response_model=list[ChatMessageOut])
def get_chat_tree(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Return all messages for this user, ordered by ltree_path
    msgs = db.query(ChatMessage).filter(ChatMessage.user_id == user.id).order_by(ChatMessage.ltree_path).all()
    return msgs

@router.get("/chat/subtree/{msg_id}", response_model=list[ChatMessageOut])
def get_subtree(msg_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Get the ltree_path for the root message
    root = db.query(ChatMessage).filter(ChatMessage.id == msg_id, ChatMessage.user_id == user.id).first()
    if not root:
        raise HTTPException(status_code=404, detail="Message not found")
    # All descendants (including root)
    msgs = db.query(ChatMessage).filter(ChatMessage.user_id == user.id, ChatMessage.ltree_path.descendant_of(root.ltree_path)).order_by(ChatMessage.ltree_path).all()
    return msgs
