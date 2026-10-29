import os
import logging
from sqlalchemy import text
from app.db.session import engine, Base
from app.config import settings

logger = logging.getLogger(__name__)

async def init_db():
    """Initializes the database tables and pgvector extension if supported."""
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    db_status = {
        "connected": False,
        "type": "unknown",
        "pgvector_available": False,
        "message": ""
    }
    
    try:
        async with engine.begin() as conn:
            # Check if PostgreSQL
            dialect = conn.dialect.name
            db_status["type"] = dialect
            
            if dialect == "postgresql":
                try:
                    await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    db_status["pgvector_available"] = True
                    logger.info("Successfully enabled pgvector extension.")
                except Exception as ext_err:
                    logger.warning(f"pgvector extension could not be enabled: {ext_err}")
                    db_status["pgvector_available"] = False
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            db_status["connected"] = True
            db_status["message"] = f"Database initialized successfully ({dialect})."
            logger.info(db_status["message"])
            
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        db_status["message"] = f"Database error: {str(e)}"
        
    return db_status
