from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import response
from app.api.routes import rag_chat
from app.api.routes import db_check

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(response.router)
app.include_router(rag_chat.router)
app.include_router(db_check.router)

# added