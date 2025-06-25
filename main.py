#!/usr/bin/env python3
"""
Memex Relay API - MCP Bridge for External Models
Bridges REST API calls to MCP server for OneNote access
"""

import asyncio
import logging
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('memex_relay.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()
API_TOKEN = os.getenv("MEMEX_RELAY_TOKEN", "memex-dev-token-2025")

# Request/Response Models
class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query for OneNote content")
    limit: Optional[int] = Field(10, description="Maximum number of results")

class GetPageRequest(BaseModel):
    page_id: str = Field(..., description="OneNote page ID to retrieve")

class WriteNoteRequest(BaseModel):
    notebook: str = Field(..., description="Target notebook name")
    page_title: str = Field(..., description="Title for the new page")
    content: str = Field(..., description="Page content in markdown format")

class SearchResult(BaseModel):
    title: str
    page_id: str
    snippet: Optional[str] = None
    notebook: Optional[str] = None

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total_count: int
    query: str

class PageContent(BaseModel):
    title: str
    content: str
    page_id: str
    notebook: Optional[str] = None
    last_modified: Optional[str] = None

class WriteResponse(BaseModel):
    status: str
    page_id: Optional[str] = None
    message: str

class NotebookInfo(BaseModel):
    id: str
    name: str
    section_count: Optional[int] = None

class ListNotebooksResponse(BaseModel):
    notebooks: List[NotebookInfo]

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: str

# For now, we'll simulate MCP calls since we need the actual MCP client
# This will be replaced with real MCP integration
async def simulate_mcp_call(tool_name: str, arguments: Dict[str, Any]) -> Any:
    """Simulate MCP calls for now - replace with real MCP client"""
    logger.info(f"Simulating MCP call: {tool_name} with args: {arguments}")
    
    if tool_name == "search_notes":
        return {
            "results": [
                {
                    "title": f"Sample result for '{arguments.get('query', '')}'",
                    "id": "sample-page-id-123",
                    "snippet": "Sample content snippet...",
                    "notebook": "Sample Notebook"
                }
            ]
        }
    elif tool_name == "get_page":
        return {
            "title": "Sample Page",
            "content": "Sample page content here...",
            "notebook": "Sample Notebook",
            "last_modified": datetime.utcnow().isoformat()
        }
    elif tool_name == "create_page":
        return {
            "page_id": "new-page-id-456",
            "status": "created"
        }
    elif tool_name == "list_notebooks":
        return {
            "notebooks": [
                {"id": "nb1", "name": "Sample Notebook 1", "section_count": 3},
                {"id": "nb2", "name": "Sample Notebook 2", "section_count": 5}
            ]
        }
    else:
        raise HTTPException(status_code=500, detail=f"Unknown tool: {tool_name}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting Memex Relay API")
    yield
    logger.info("Shutting down Memex Relay API")

# FastAPI App
app = FastAPI(
    title="Memex Relay API",
    description="MCP Bridge for External Models - OneNote Access",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth dependency
async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify API token"""
    if credentials.credentials != API_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )
    return credentials.credentials

# Utility functions
def create_error_response(error: str, detail: str = None) -> Dict:
    """Create standardized error response"""
    return {
        "error": error,
        "detail": detail,
        "timestamp": datetime.utcnow().isoformat()
    }

# API Endpoints
@app.get("/")
async def root():
    """API health check"""
    return {
        "service": "Memex Relay API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "note": "This is a simulation - replace with real MCP integration"
    }

@app.post("/v1/search", response_model=SearchResponse)
async def search_notebooks(
    request: SearchRequest,
    token: str = Depends(verify_token)
):
    """Search OneNote notebooks for query"""
    logger.info(f"Search request: {request.query}")
    
    try:
        # Call simulated MCP search tool
        result = await simulate_mcp_call("search_notes", {
            "query": request.query,
            "limit": request.limit
        })
        
        # Transform result to API format
        search_results = []
        for item in result.get("results", []):
            search_results.append(SearchResult(
                title=item.get("title", ""),
                page_id=item.get("id", ""),
                snippet=item.get("snippet", ""),
                notebook=item.get("notebook", "")
            ))
        
        return SearchResponse(
            results=search_results,
            total_count=len(search_results),
            query=request.query
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/get_page", response_model=PageContent)
async def get_page(
    request: GetPageRequest,
    token: str = Depends(verify_token)
):
    """Retrieve full OneNote page content"""
    logger.info(f"Get page request: {request.page_id}")
    
    try:
        # Call simulated MCP get page tool
        result = await simulate_mcp_call("get_page", {
            "page_id": request.page_id
        })
        
        return PageContent(
            title=result.get("title", ""),
            content=result.get("content", ""),
            page_id=request.page_id,
            notebook=result.get("notebook", ""),
            last_modified=result.get("last_modified", "")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get page failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/write_note", response_model=WriteResponse)
async def write_note(
    request: WriteNoteRequest,
    token: str = Depends(verify_token)
):
    """Create new OneNote page"""
    logger.info(f"Write note request: {request.page_title} in {request.notebook}")
    
    try:
        # Call simulated MCP create page tool
        result = await simulate_mcp_call("create_page", {
            "notebook": request.notebook,
            "title": request.page_title,
            "content": request.content
        })
        
        return WriteResponse(
            status="success",
            page_id=result.get("page_id", ""),
            message=f"Page '{request.page_title}' created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Write note failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/notebooks", response_model=ListNotebooksResponse)
async def list_notebooks(token: str = Depends(verify_token)):
    """List available OneNote notebooks"""
    logger.info("List notebooks request")
    
    try:
        # Call simulated MCP list notebooks tool
        result = await simulate_mcp_call("list_notebooks", {})
        
        notebooks = []
        for nb in result.get("notebooks", []):
            notebooks.append(NotebookInfo(
                id=nb.get("id", ""),
                name=nb.get("name", ""),
                section_count=nb.get("section_count", 0)
            ))
        
        return ListNotebooksResponse(notebooks=notebooks)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List notebooks failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return create_error_response(
        error=f"HTTP {exc.status_code}",
        detail=exc.detail
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return create_error_response(
        error="Internal server error",
        detail="An unexpected error occurred"
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=5000,
        reload=True,
        log_level="info"
    )