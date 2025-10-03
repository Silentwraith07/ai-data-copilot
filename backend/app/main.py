# FastAPI main application
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import shutil
from pathlib import Path
from typing import Optional
import uvicorn

from app.config import settings
from app.models.schemas import FileUploadResponse, QueryRequest, QueryResponse
from app.modules.file_ingestion import FileIngestionModule
from app.modules.llm_query import LLMQueryModule
from app.modules.visualization import VisualizationModule

# Initialize FastAPI app
app = FastAPI(
    title="AI Data Copilot API",
    description="Backend API for AI-powered data analysis and visualization",
    version="1.0.0"
)

# CORS middleware for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize modules
file_ingestion = FileIngestionModule(settings.UPLOAD_DIR)
llm_query = LLMQueryModule(settings.OPENAI_API_KEY, settings.OPENAI_MODEL)
visualization = VisualizationModule()

# Simple API key authentication
async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """
    Simple API key verification.
    Extensible to OAuth2/JWT for production.
    """
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "online", "service": "AI Data Copilot API"}

@app.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    """
    Upload CSV/Excel file and extract schema + summary.
    
    Returns:
        - file_id: Unique identifier for the uploaded file
        - schema: Column names and data types
        - summary: Statistical summary
        - sample_rows: First 5 rows
    """
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # Save uploaded file temporarily
    temp_path = Path(settings.UPLOAD_DIR) / f"temp_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Ingest and process file
        file_id, metadata = file_ingestion.ingest_file(str(temp_path), file.filename)
        
        # Clean up temp file
        temp_path.unlink()
        
        return FileUploadResponse(**metadata)
        
    except Exception as e:
        # Clean up on error
        if temp_path.exists():
            temp_path.unlink()
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query_data(
    request: QueryRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Process natural language query on uploaded data.
    
    Returns:
        - answer_text: Natural language answer
        - chart_type: Suggested visualization type
        - chart_data: Structured data for chart rendering
        - recommendations: Actionable insights
    """
    try:
        # Retrieve dataframe and metadata
        df = file_ingestion.get_dataframe(request.file_id)
        metadata = file_ingestion.get_metadata(request.file_id)
        
        # Process query with LLM
        result = llm_query.process_query(
            question=request.question,
            df=df,
            schema=metadata["schema"],
            summary=metadata["summary"]
        )
        
        return QueryResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/files/{file_id}/metadata")
async def get_file_metadata(
    file_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Retrieve metadata for a previously uploaded file.
    """
    try:
        metadata = file_ingestion.get_metadata(file_id)
        return metadata
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
