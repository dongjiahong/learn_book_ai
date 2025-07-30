from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.questions import router as questions_router
from app.api.rag import router as rag_router
from app.api.evaluation import router as evaluation_router
from app.api.learning import router as learning_router
from app.api.knowledge_points import router as knowledge_points_router
from app.api.review import router as review_router
from app.api.anki import router as anki_router
from app.core.config import config
from app.services.document_processor import document_processor

app = FastAPI(
    title="RAG Learning Platform API",
    description="A RAG-based learning platform API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_allow_origins,
    allow_credentials=config.cors_allow_credentials,
    allow_methods=config.cors_allow_methods,
    allow_headers=config.cors_allow_headers,
)

# Include routers
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(questions_router)
app.include_router(rag_router)
app.include_router(evaluation_router)
app.include_router(learning_router)
app.include_router(knowledge_points_router)
app.include_router(review_router)
app.include_router(anki_router)

@app.get("/")
async def root():
    return {"message": "RAG Learning Platform API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    document_processor.stop()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8800)