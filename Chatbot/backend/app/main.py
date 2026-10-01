from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings

app = FastAPI(
    title="Multimodal AI Chatbot",
    description="A beginner-friendly Multimodal AI Chatbot MVP built with React, FastAPI, Python and PostgreSQL.",
    version="0.1.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For MVP, allow all origins. In production, restrict this.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Multimodal AI Chatbot API"}

from app.api import chat, documents, search, audio, files

app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(audio.router, prefix="/api", tags=["audio"])
app.include_router(files.router, prefix="/api/files", tags=["files"])

