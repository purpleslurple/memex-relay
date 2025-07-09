#!/usr/bin/env python3
"""
Direct OneNote Integration for Memex Relay API
Uses OneNote functions directly instead of MCP subprocess calls
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
import msal
import httpx

logger = logging.getLogger(__name__)

# Microsoft Graph API constants
GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
SCOPES = [
    "https://graph.microsoft.com/Notes.Read",
    "https://graph.microsoft.com/Notes.ReadWrite",
    "https://graph.microsoft.com/User.Read"
]

# Token cache configuration
TOKEN_CACHE_ENABLED = os.getenv("ONENOTE_CACHE_TOKENS", "true").lower() in ("true", "1", "yes")
TOKEN_CACHE_FILE = Path.home() / ".onenote_mcp_tokens.json"

class DirectOneNoteClient:
    """Direct OneNote client using the same auth as MCP server"""
    
    def __init__(self):
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[float] = None
        self.msal_app: Optional[msal.PublicClientApplication] = None
        
    def get_client_id(self) -> str:
        """Get the Azure client ID from environment variable."""
        client_id = os.getenv("AZURE_CLIENT_ID")
        if not client_id:
            raise Exception("AZURE_CLIENT_ID environment variable not set")
        return client_id

    def load_tokens(self) -> bool:
        """Load tokens from the same cache file as MCP server"""
        if not TOKEN_CACHE_ENABLED:
            return False
            
        try:
            if not TOKEN_CACHE_FILE.exists():
                return False
                
            with open(TOKEN_CACHE_FILE, 'r') as f:
                token_data = json.load(f)
            
            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token")
            self.token_expires_at = token_data.get("expires_at")
            
            # Check if token is still valid
            if self.token_expires_at and time.time() < self.token_expires_at:
                logger.info("Valid tokens loaded from MCP server cache")
                return True
            else:
                logger.info("Cached tokens expired")
                return False
                
        except Exception as e:
            logger.warning(f"Failed to load tokens: {e}")
            return False

    async def ensure_valid_token(self) -> bool:
        """Ensure we have a valid access token"""
        # First, try loading cached tokens from MCP server
        if not self.access_token:
            self.load_tokens()
        
        # Check if current token is still valid
        if self.access_token and self.token_expires_at and time.time() < self.token_expires_at:
            return True
        
        # No valid token available
        self.access_token = None
        return False

    async def make_graph_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
        """Make a request to Microsoft Graph API."""
        if not await self.ensure_valid_token():
            raise Exception("Not authenticated. Please authenticate through OneNote MCP server first.")
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{GRAPH_BASE_URL}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=data)
            elif method == "PATCH":
                response = await client.patch(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
        
        if response.status_code >= 400:
            raise Exception(f"Graph API error: {response.status_code} - {response.text}")
        
        return response.json()

    async def check_authentication(self) -> Dict[str, Any]:
        """Check if we have valid authentication"""
        try:
            if await self.ensure_valid_token():
                user_info = await self.make_graph_request("/me")
                time_until_expiry = int(self.token_expires_at - time.time()) if self.token_expires_at else 0
                
                return {
                    "status": "authenticated",
                    "user": user_info.get("displayName", "Unknown"),
                    "email": user_info.get("mail") or user_info.get("userPrincipalName", "Unknown"),
                    "token_valid_for_seconds": max(0, time_until_expiry),
                    "source": "mcp_server_cache"
                }
            else:
                return {
                    "status": "not_authenticated",
                    "message": "Please authenticate through OneNote MCP server first",
                    "source": "mcp_server_cache"
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def list_notebooks(self) -> Dict[str, Any]:
        """List all OneNote notebooks"""
        try:
            notebooks = await self.make_graph_request("/me/onenote/notebooks")
            
            result = []
            for notebook in notebooks.get("value", []):
                # Get section count for each notebook
                try:
                    sections = await self.make_graph_request(f"/me/onenote/notebooks/{notebook.get('id')}/sections")
                    section_count = len(sections.get("value", []))
                except:
                    section_count = 0
                    
                result.append({
                    "id": notebook.get("id"),
                    "name": notebook.get("displayName"),
                    "section_count": section_count
                })
            
            return {"notebooks": result}
            
        except Exception as e:
            logger.error(f"Error listing notebooks: {e}")
            raise

    async def list_sections(self, notebook_id: str) -> Dict[str, Any]:
        """List sections in a specific notebook"""
        try:
            sections = await self.make_graph_request(f"/me/onenote/notebooks/{notebook_id}/sections")
            
            result = []
            for section in sections.get("value", []):
                # Get page count for each section
                try:
                    pages = await self.make_graph_request(f"/me/onenote/sections/{section.get('id')}/pages")
                    page_count = len(pages.get("value", []))
                except:
                    page_count = 0
                    
                result.append({
                    "id": section.get("id"),
                    "name": section.get("displayName"),
                    "page_count": page_count,
                    "created": section.get("createdDateTime"),
                    "modified": section.get("lastModifiedDateTime")
                })
            
            return {"sections": result}
            
        except Exception as e:
            logger.error(f"Error listing sections: {e}")
            raise

    async def list_pages(self, section_id: str) -> Dict[str, Any]:
        """List pages in a specific section"""
        try:
            pages = await self.make_graph_request(f"/me/onenote/sections/{section_id}/pages")
            
            result = []
            for page in pages.get("value", []):
                result.append({
                    "id": page.get("id"),
                    "title": page.get("title"),
                    "created": page.get("createdDateTime"),
                    "modified": page.get("lastModifiedDateTime"),
                    "content_url": page.get("contentUrl")
                })
            
            return {"pages": result}
            
        except Exception as e:
            logger.error(f"Error listing pages: {e}")
            raise

    async def search_notes(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search OneNote for content matching the query"""
        try:
            # OneNote Graph API doesn't have a direct search endpoint
            # We'll search through notebooks, sections, and pages
            
            search_results = []
            notebooks = await self.make_graph_request("/me/onenote/notebooks")
            
            for notebook in notebooks.get("value", [])[:5]:  # Limit to first 5 notebooks
                notebook_id = notebook.get("id")
                notebook_name = notebook.get("displayName", "")
                
                try:
                    # Get sections in this notebook
                    sections = await self.make_graph_request(f"/me/onenote/notebooks/{notebook_id}/sections")
                    
                    for section in sections.get("value", [])[:3]:  # Limit sections
                        section_id = section.get("id")
                        
                        try:
                            # Get pages in this section
                            pages = await self.make_graph_request(f"/me/onenote/sections/{section_id}/pages")
                            
                            for page in pages.get("value", [])[:10]:  # Limit pages
                                page_title = page.get("title", "")
                                page_id = page.get("id")
                                
                                # Simple search - check if query appears in title
                                if query.lower() in page_title.lower():
                                    search_results.append({
                                        "title": page_title,
                                        "id": page_id,
                                        "snippet": f"Found in page title: {page_title[:100]}...",
                                        "notebook": notebook_name
                                    })
                                    
                                    if len(search_results) >= limit:
                                        break
                                        
                        except Exception as e:
                            logger.debug(f"Error searching section {section_id}: {e}")
                            continue
                            
                        if len(search_results) >= limit:
                            break
                            
                except Exception as e:
                    logger.debug(f"Error searching notebook {notebook_id}: {e}")
                    continue
                    
                if len(search_results) >= limit:
                    break
            
            return {"results": search_results}
            
        except Exception as e:
            logger.error(f"Error searching notes: {e}")
            # Return a fallback result
            return {
                "results": [{
                    "title": f"Search for '{query}' - Authentication or API error",
                    "id": "error-result",
                    "snippet": f"Error: {str(e)}",
                    "notebook": "Error"
                }]
            }

    async def get_page_content(self, page_id: str) -> Dict[str, Any]:
        """Get content of a specific page"""
        try:
            # Get page content (returns HTML)
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.access_token}"}
                response = await client.get(
                    f"{GRAPH_BASE_URL}/me/onenote/pages/{page_id}/content",
                    headers=headers
                )
                
                if response.status_code >= 400:
                    raise Exception(f"Error getting page content: {response.status_code} - {response.text}")
                
                content = response.text
                
            # Also get page metadata
            page_info = await self.make_graph_request(f"/me/onenote/pages/{page_id}")
            
            return {
                "title": page_info.get("title", "Unknown Title"),
                "content": content,
                "notebook": "Unknown",  # TODO: Get notebook info
                "last_modified": page_info.get("lastModifiedDateTime")
            }
            
        except Exception as e:
            logger.error(f"Error getting page content: {e}")
            raise

    async def create_page(self, notebook: str, title: str, content: str) -> Dict[str, Any]:
        """Create a new page in OneNote"""
        try:
            # First, find the notebook by name
            notebooks = await self.make_graph_request("/me/onenote/notebooks")
            
            target_notebook = None
            for nb in notebooks.get("value", []):
                if nb.get("displayName", "").lower() == notebook.lower():
                    target_notebook = nb
                    break
            
            if not target_notebook:
                raise Exception(f"Notebook '{notebook}' not found")
            
            # Get the first section in the notebook
            sections = await self.make_graph_request(f"/me/onenote/notebooks/{target_notebook['id']}/sections")
            
            if not sections.get("value"):
                raise Exception(f"No sections found in notebook '{notebook}'")
            
            section_id = sections["value"][0]["id"]
            
            # Create the page HTML
            page_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <meta name="created" content="{time.strftime('%Y-%m-%dT%H:%M:%S.0000000')}" />
</head>
<body>
    <div>
        <h1>{title}</h1>
        <div>{content}</div>
    </div>
</body>
</html>"""
            
            # Create the page
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/xhtml+xml"
                }
                
                response = await client.post(
                    f"{GRAPH_BASE_URL}/me/onenote/sections/{section_id}/pages",
                    headers=headers,
                    content=page_html
                )
                
                if response.status_code >= 400:
                    raise Exception(f"Error creating page: {response.status_code} - {response.text}")
                
                page = response.json()
            
            return {
                "page_id": page.get("id"),
                "status": "created"
            }
            
        except Exception as e:
            logger.error(f"Error creating page: {e}")
            raise

    async def update_page_content(self, page_id: str, content_html: str, target_element: str = "body") -> Dict[str, Any]:
        """Update the content of an existing OneNote page"""
        try:
            # OneNote Graph API uses PATCH for content updates
            # The content needs to be properly formatted HTML with the target element
            
            # For OneNote, we need to send a PATCH request with the HTML content
            # The target_element parameter specifies where to insert the content
            patch_data = [
                {
                    "target": target_element,
                    "action": "append",
                    "content": content_html
                }
            ]
            
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                response = await client.patch(
                    f"{GRAPH_BASE_URL}/me/onenote/pages/{page_id}/content",
                    headers=headers,
                    json=patch_data
                )
                
                if response.status_code >= 400:
                    raise Exception(f"Error updating page content: {response.status_code} - {response.text}")
            
            return json.dumps({
                "status": "success",
                "message": "Page content updated successfully",
                "page_id": page_id
            })
            
        except Exception as e:
            logger.error(f"Error updating page content: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    async def create_notebook(self, name: str, description: str = None) -> str:
        """Create a new OneNote notebook"""
        try:
            # Create notebook data
            notebook_data = {
                "displayName": name
            }
            
            # Create the notebook
            result = await self.make_graph_request("/me/onenote/notebooks", "POST", notebook_data)
            
            return json.dumps({
                "status": "success",
                "message": f"Notebook '{name}' created successfully",
                "notebook": {
                    "id": result.get("id"),
                    "name": result.get("displayName")
                }
            })
            
        except Exception as e:
            logger.error(f"Error creating notebook: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    async def create_section(self, notebook_id: str, name: str) -> str:
        """Create a new section in a OneNote notebook"""
        try:
            # Create section data
            section_data = {
                "displayName": name
            }
            
            # Create the section
            result = await self.make_graph_request(f"/me/onenote/notebooks/{notebook_id}/sections", "POST", section_data)
            
            return json.dumps({
                "status": "success",
                "message": f"Section '{name}' created successfully",
                "section": {
                    "id": result.get("id"),
                    "name": result.get("displayName")
                }
            })
            
        except Exception as e:
            logger.error(f"Error creating section: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    async def create_page_by_section(self, section_id: str, title: str, content_html: str = None) -> str:
        """Create a new page in a specific OneNote section using section ID"""
        try:
            # Create the page HTML
            if content_html:
                # Use provided HTML content
                if not content_html.strip().startswith('<html>'):
                    page_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <meta name="created" content="{time.strftime('%Y-%m-%dT%H:%M:%S.0000000')}" />
</head>
<body>
    <div>
        <h1>{title}</h1>
        <div>{content_html}</div>
    </div>
</body>
</html>"""
                else:
                    page_html = content_html
            else:
                # Create a basic page with just the title
                page_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <meta name="created" content="{time.strftime('%Y-%m-%dT%H:%M:%S.0000000')}" />
</head>
<body>
    <div>
        <h1>{title}</h1>
        <p>Page created by Memex Relay API</p>
    </div>
</body>
</html>"""
            
            # Create the page
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/xhtml+xml"
                }
                
                response = await client.post(
                    f"{GRAPH_BASE_URL}/me/onenote/sections/{section_id}/pages",
                    headers=headers,
                    content=page_html
                )
                
                if response.status_code >= 400:
                    raise Exception(f"Error creating page: {response.status_code} - {response.text}")
                
                page = response.json()
            
            return json.dumps({
                "status": "success",
                "message": f"Page '{title}' created successfully",
                "page": {
                    "id": page.get("id"),
                    "title": page.get("title"),
                    "created": page.get("createdDateTime"),
                    "content_url": page.get("contentUrl")
                }
            })
            
        except Exception as e:
            logger.error(f"Error creating page by section: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    async def clear_token_cache(self) -> str:
        """Clear the stored authentication tokens"""
        try:
            self.access_token = None
            self.refresh_token = None
            self.token_expires_at = None
            
            # Also clear the cache file if it exists
            if TOKEN_CACHE_FILE.exists():
                TOKEN_CACHE_FILE.unlink()
            
            return json.dumps({
                "status": "success",
                "message": "Token cache cleared"
            })
            
        except Exception as e:
            logger.error(f"Error clearing token cache: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

# Global instance
onenote_client = DirectOneNoteClient()
