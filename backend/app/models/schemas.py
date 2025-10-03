# Pydantic models for request/response validation
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any

class FileUploadResponse(BaseModel):
    """Response model for file upload endpoint"""
    file_id: str
    filename: str
    schema: Dict[str, str]
    summary: Dict[str, Any]
    sample_rows: List[Dict[str, Any]]
    row_count: int
    column_count: int

class QueryRequest(BaseModel):
    """Request model for natural language query"""
    file_id: str
    question: str = Field(..., min_length=1, description="Natural language question about the data")

class ChartData(BaseModel):
    """Structured chart data"""
    labels: Optional[List[str]] = None
    datasets: Optional[List[Dict[str, Any]]] = None
    x_column: Optional[str] = None
    y_column: Optional[str] = None

class QueryResponse(BaseModel):
    """Response model for query endpoint with LLM-generated insights"""
    answer_text: str
    chart_type: Optional[str] = None  # bar, line, pie, scatter, none
    chart_data: Optional[ChartData] = None
    recommendations: Optional[List[str]] = None
    sql_query: Optional[str] = None  # For transparency
