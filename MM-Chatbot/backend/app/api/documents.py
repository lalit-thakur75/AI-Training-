import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.document import Document, DocumentVersion
from app.models.chunk import DocumentChunk
from app.schemas.document import (
    DocumentResponse,
    DocumentVersionResponse,
    DocumentCreateRequest,
    DocumentUpdateRequest,
    DocumentAIEditRequest
)
from app.services.document_service import DocumentService
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Uploads a supported document (PDF, TXT, DOCX), extracts text,
    stores metadata and version 1, and indexes chunks into pgvector for RAG.
    """
    file_bytes = await file.read()
    if not DocumentService.is_valid_document(file.filename, len(file_bytes)):
        raise HTTPException(
            status_code=400,
            detail="Unsupported format or file exceeds 15MB. Supported: .pdf, .txt, .docx"
        )

    safe_path = DocumentService.get_safe_storage_path(file.filename)
    with open(safe_path, "wb") as f:
        f.write(file_bytes)

    # Extract text
    try:
        extracted_text = DocumentService.extract_text(safe_path)
    except Exception as e:
        if os.path.exists(safe_path):
            os.remove(safe_path)
        raise HTTPException(status_code=400, detail=f"Text extraction failed: {str(e)}")

    # Create document record
    doc = Document(
        filename=file.filename,
        storage_path=safe_path,
        content_type=file.content_type or "application/octet-stream",
        current_version=1
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Create Initial Version 1
    version_1 = DocumentVersion(
        document_id=doc.id,
        version_number=1,
        content=extracted_text,
        change_summary="Original uploaded file"
    )
    db.add(version_1)
    await db.commit()

    # Chunk and Index for RAG
    chunks = DocumentService.chunk_text(extracted_text)
    if chunks:
        await RAGService.index_document_chunks(db, doc.id, chunks, file.filename)

    return doc


@router.get("", response_model=List[DocumentResponse])
async def list_documents(db: AsyncSession = Depends(get_db)):
    """Lists all stored documents."""
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    return result.scalars().all()


@router.get("/{document_id}")
async def get_document(document_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves document details with the latest content."""
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Fetch latest version content
    stmt = (
        select(DocumentVersion)
        .where(DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.version_number.desc())
        .limit(1)
    )
    latest_version = (await db.execute(stmt)).scalar_one_or_none()

    return {
        "id": doc.id,
        "filename": doc.filename,
        "content_type": doc.content_type,
        "current_version": doc.current_version,
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
        "content": latest_version.content if latest_version else ""
    }


@router.post("/create", response_model=DocumentResponse)
async def create_document(
    request: DocumentCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Creates a new text document directly in the workspace."""
    safe_path = DocumentService.get_safe_storage_path(request.filename)
    with open(safe_path, "w", encoding="utf-8") as f:
        f.write(request.content)

    doc = Document(
        filename=request.filename,
        storage_path=safe_path,
        content_type="text/plain",
        current_version=1
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    v1 = DocumentVersion(
        document_id=doc.id,
        version_number=1,
        content=request.content,
        change_summary="Created in workspace"
    )
    db.add(v1)
    await db.commit()

    # Index for RAG
    chunks = DocumentService.chunk_text(request.content)
    if chunks:
        await RAGService.index_document_chunks(db, doc.id, chunks, request.filename)

    return doc


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    request: DocumentUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Saves an updated document version without overwriting the original.
    Automatically re-indexes chunks into pgvector so RAG stays synchronized.
    """
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Increment version
    new_version_num = doc.current_version + 1
    doc.current_version = new_version_num

    # Add new version entry
    new_version = DocumentVersion(
        document_id=doc.id,
        version_number=new_version_num,
        content=request.content,
        change_summary=request.change_summary or f"Version {new_version_num}"
    )
    db.add(new_version)
    await db.commit()
    await db.refresh(doc)

    # Re-index RAG chunks with updated content
    chunks = DocumentService.chunk_text(request.content)
    if chunks:
        await RAGService.index_document_chunks(db, doc.id, chunks, doc.filename)

    return doc


@router.get("/{document_id}/versions", response_model=List[DocumentVersionResponse])
async def get_document_versions(document_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves all version records for a document."""
    stmt = (
        select(DocumentVersion)
        .where(DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.version_number.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/{document_id}/ai-edit")
async def ai_edit_document(
    document_id: str,
    request: DocumentAIEditRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Applies AI transformations (summarize, grammar, expand, custom) to document content.
    Returns the proposed preview without committing changes to disk.
    """
    # Fetch latest content
    stmt = (
        select(DocumentVersion)
        .where(DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.version_number.desc())
        .limit(1)
    )
    latest_version = (await db.execute(stmt)).scalar_one_or_none()
    if not latest_version:
        raise HTTPException(status_code=404, detail="Document has no content")

    action = request.action
    instruction = ""
    if action == "summarize":
        instruction = "Provide a clear, well-structured executive summary of the following document content."
    elif action == "grammar":
        instruction = "Correct all grammatical, spelling, and punctuation errors in the following text while preserving its tone and meaning."
    elif action == "expand":
        instruction = "Expand upon the key ideas in the following text with greater detail, depth, and clarity."
    elif action == "custom":
        instruction = request.custom_instruction or "Refine and improve the following text."
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    prompt = f"{instruction}\n\n[DOCUMENT CONTENT]:\n{latest_version.content[:6000]}"
    ai_result = await LLMService.generate_response(
        messages=[{"role": "user", "content": prompt}],
        system_prompt="You are a professional editor and writer helping the user refine their document."
    )

    return {
        "action": action,
        "original_content": latest_version.content,
        "proposed_content": ai_result
    }
