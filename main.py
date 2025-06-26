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

from fastapi import FastAPI, HTTPException, Depends, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field
import uvicorn

# Import the MCP client for real OneNote integration
from mcp_client import onenote_client

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

class ListSectionsRequest(BaseModel):
    notebook_id: str = Field(..., description="OneNote notebook ID")

class ListPagesRequest(BaseModel):
    section_id: str = Field(..., description="OneNote section ID")

class SectionInfo(BaseModel):
    id: str
    name: str
    page_count: Optional[int] = None
    created: Optional[str] = None
    modified: Optional[str] = None

class ListSectionsResponse(BaseModel):
    sections: List[SectionInfo]

class PageInfo(BaseModel):
    id: str
    title: str
    created: Optional[str] = None
    modified: Optional[str] = None
    content_url: Optional[str] = None

class ListPagesResponse(BaseModel):
    pages: List[PageInfo]

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

class NotebookListResponse(BaseModel):
    notebooks: List[str]

class PageListResponse(BaseModel):
    pages: List[str]

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting Memex Relay API with real OneNote MCP integration")
    
    # Check OneNote authentication status on startup
    try:
        auth_status = await onenote_client.check_authentication()
        logger.info(f"OneNote auth status: {auth_status.get('status', 'unknown')}")
    except Exception as e:
        logger.warning(f"Could not check OneNote auth status: {e}")
    
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

# Ngrok bypass middleware
@app.middleware("http")
async def add_ngrok_bypass_header(request: Request, call_next):
    """Add ngrok-skip-browser-warning header to all responses"""
    response = await call_next(request)
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response

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
    # Check authentication status for the health check
    auth_status = await onenote_client.check_authentication()
    
    return {
        "service": "Memex Relay API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "onenote_auth": auth_status.get("status", "unknown"),
        "note": "Connected to real OneNote MCP server"
    }

@app.post("/v1/search", response_model=SearchResponse)
async def search_notebooks(
    request: SearchRequest,
    token: str = Depends(verify_token)
):
    """Search OneNote notebooks for query"""
    logger.info(f"Search request: {request.query}")
    
    try:
        # Call real MCP search tool
        result = await onenote_client.search_notes(request.query, request.limit)
        
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
        # Call real MCP get page tool
        result = await onenote_client.get_page_content(request.page_id)
        
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
        # Call real MCP create page tool
        result = await onenote_client.create_page(
            request.notebook, 
            request.page_title, 
            request.content
        )
        
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

@app.get("/v1/notebooks", response_model=NotebookListResponse)
async def list_notebooks(token: str = Depends(verify_token)):
    """List available OneNote notebooks"""
    logger.info("List notebooks request")
    
    try:
        # Call real MCP list notebooks tool
        result = await onenote_client.list_notebooks()
        
        # Transform to match schema expectation (array of strings)
        notebook_names = [nb.get("name", "") for nb in result.get("notebooks", [])]
        
        return NotebookListResponse(notebooks=notebook_names)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List notebooks failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/notebooks/{notebook_id}/sections", response_model=ListSectionsResponse)
async def get_notebook_sections(
    notebook_id: str,
    token: str = Depends(verify_token)
):
    """List sections in a specific notebook (REST style)"""
    logger.info(f"GET sections request for notebook: {notebook_id}")
    
    try:
        # Call real MCP list sections tool
        result = await onenote_client.list_sections(notebook_id)
        
        sections = []
        for section in result.get("sections", []):
            sections.append(SectionInfo(
                id=section.get("id", ""),
                name=section.get("name", ""),
                page_count=section.get("page_count", 0),
                created=section.get("created"),
                modified=section.get("modified")
            ))
        
        return ListSectionsResponse(sections=sections)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GET sections failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/sections/{section_id}/pages", response_model=ListPagesResponse)
async def get_section_pages(
    section_id: str,
    token: str = Depends(verify_token)
):
    """List pages in a specific section (REST style)"""
    logger.info(f"GET pages request for section: {section_id}")
    
    try:
        # Call real MCP list pages tool
        result = await onenote_client.list_pages(section_id)
        
        pages = []
        for page in result.get("pages", []):
            pages.append(PageInfo(
                id=page.get("id", ""),
                title=page.get("title", ""),
                created=page.get("created"),
                modified=page.get("modified"),
                content_url=page.get("content_url")
            ))
        
        return ListPagesResponse(pages=pages)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GET pages failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/v1/notebooks/{notebook_id}/pages", response_model=PageListResponse)
async def get_notebook_pages(
    notebook_id: str,
    token: str = Depends(verify_token)
):
    """List all pages in a notebook (flattened from all sections)"""
    logger.info(f"GET all pages request for notebook: {notebook_id}")
    
    try:
        # First get all sections in the notebook
        sections_result = await onenote_client.list_sections(notebook_id)
        
        all_pages = []
        for section in sections_result.get("sections", []):
            section_id = section.get("id")
            try:
                # Get pages from each section
                pages_result = await onenote_client.list_pages(section_id)
                all_pages.extend(pages_result.get("pages", []))
            except Exception as e:
                logger.debug(f"Error getting pages from section {section_id}: {e}")
                continue
        
        # Transform to match schema expectation (array of strings)
        page_titles = [page.get("title", "") for page in all_pages]
        
        return PageListResponse(pages=page_titles)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GET notebook pages failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/pages/{page_id}", response_model=PageContent)
async def get_page_by_id(
    page_id: str,
    token: str = Depends(verify_token)
):
    """Get content of a specific page by ID"""
    logger.info(f"GET page content request: {page_id}")
    
    try:
        # Call real MCP get page tool
        result = await onenote_client.get_page_content(page_id)
        
        return PageContent(
            title=result.get("title", ""),
            content=result.get("content", ""),
            page_id=page_id,
            notebook=result.get("notebook", ""),
            last_modified=result.get("last_modified", "")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GET page by ID failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# New endpoint for checking OneNote authentication
@app.get("/v1/auth/status")
async def auth_status(token: str = Depends(verify_token)):
    """Check OneNote authentication status"""
    try:
        result = await onenote_client.check_authentication()
        return result
    except Exception as e:
        logger.error(f"Auth status check failed: {e}")
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
