# Memex Relay API

A production-ready REST API bridge that enables non-MCP AI models (like ChatGPT) to access OneNote through your MCP server. This creates a unified knowledge access layer across different AI ecosystems.

For a complete OneNote MCP server implementation, see: https://github.com/purpleslurple/onenote-mcp-server

## Architecture

**Data Flow:** User → ChatGPT → Memex Relay API → MCP Server → OneNote

The Memex Relay translates REST API calls into MCP protocol messages, enabling any HTTP-capable AI model to access your OneNote knowledge base.

## Quick Start

1. **Install dependencies:**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

2. **Activate environment and run:**
   ```bash
   source memex_relay_env/bin/activate
   python main.py
   ```

3. **Test the API:**
   ```bash
   python test_api.py
   ```

4. **Health check all services:**
   ```bash
   chmod +x service_health_check.sh
   ./service_health_check.sh
   ```

## API Endpoints

### Core Operations
- `GET /` - Health check with OneNote auth status
- `POST /v1/get_page` - Retrieve full page content by ID
- `POST /v1/write_note` - Create new OneNote pages
- `GET /v1/notebooks` - List available notebooks

### Navigation & Discovery
- `GET /v1/notebooks/{notebook_id}/sections` - List sections by notebook ID
- `GET /v1/notebooks/{notebook_name}/sections` - List sections by notebook name
- `GET /v1/sections/{section_id}/pages` - List pages by section ID
- `GET /v1/notebooks/{notebook_name}/pages` - List all pages in notebook (flattened)
- `GET /v1/notebooks/{notebook_name}/sections/{section_name}/pages` - Pages by names
- `GET /v1/pages/{page_id}` - Get page content by ID

### Management Operations
- `POST /v1/notebooks` - Create new notebooks
- `POST /v1/sections` - Create new sections
- `POST /v1/pages/update` - Update existing page content

### Authentication Management
- `GET /v1/auth/status` - Check OneNote authentication status
- `POST /v1/auth/clear_cache` - Clear stored authentication tokens

## Authentication

All endpoints (except health check) require Bearer token authentication:
```
Authorization: Bearer memex-dev-token-2025
```

Set custom token via environment variable:
```bash
export MEMEX_RELAY_TOKEN="your-custom-token"
```

## Request/Response Examples

### Create a New Page
```bash
curl -X POST http://localhost:5000/v1/write_note \
  -H "Authorization: Bearer memex-dev-token-2025" \
  -H "Content-Type: application/json" \
  -d '{
    "notebook": "Claude Conversations",
    "page_title": "API Test Page",
    "content": "# Hello from Memex Relay\n\nThis page was created via API!"
  }'
```

### Get Page Content
```bash
curl -X POST http://localhost:5000/v1/get_page \
  -H "Authorization: Bearer memex-dev-token-2025" \
  -H "Content-Type: application/json" \
  -d '{"page_id": "your-page-id-here"}'
```

### List Notebooks
```bash
curl -X GET http://localhost:5000/v1/notebooks \
  -H "Authorization: Bearer memex-dev-token-2025"
```

## Integration Status

✅ **Real OneNote MCP Integration** - Connected to production OneNote MCP server  
✅ **Bearer Token Authentication** - Secure API access  
✅ **Comprehensive Error Handling** - Detailed logging and graceful failures  
✅ **CORS Support** - Ready for web application integration  
✅ **Health Monitoring** - Service status and auth validation

## Custom GPT Integration

Use the provided `custom_gpt_schema.json` to configure ChatGPT with direct access to this API. This enables natural language queries against your OneNote knowledge base.

**Available Schema Files:**
- `custom_gpt_schema.json` - Current production schema
- `custom_gpt_schema_claude_capable.json` - Enhanced Claude-compatible version
- `custom_gpt_schema_original.json` - Original design reference

## Multi-Agent Memory Bus

This API enables the **Multi-Agent Memory Bus** - a three-way AI collaboration system where:
- **Claude** accesses OneNote via direct MCP integration
- **ChatGPT (G)** accesses OneNote via this Memex Relay API
- **Human users** access OneNote via native interface

All three participants can collaborate in real-time with persistent shared memory.

## Service Health Monitoring

The `service_health_check.sh` script provides comprehensive status checking:

```bash
./service_health_check.sh
```

**Validates:**
- ngrok tunnel status (port 4040)
- Memex Relay API health (port 5000)
- OneNote integration functionality
- Authentication status

## Development & Debugging

### Logging
Check `memex_relay.log` for detailed request/response logging and debugging information.

### Environment Setup
The API runs on `localhost:5000` by default. For external access, use ngrok:
```bash
ngrok http 5000
```

### Testing Suite
Run the automated test suite:
```bash
python test_api.py
```

## Technical Architecture

**Framework:** FastAPI with async/await support  
**Authentication:** Bearer token with configurable secrets  
**OneNote Integration:** Real MCP client via `mcp_client.py`  
**Error Handling:** Comprehensive logging and graceful failure modes  
**CORS:** Configured for local development and production use

## Status

**Production Ready** - Real OneNote integration, comprehensive API surface, robust error handling, and multi-agent collaboration capabilities. This bridge enables true cross-AI knowledge sharing through a unified substrate.