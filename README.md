# Memex Relay API

A REST API bridge that allows non-MCP models (like ChatGPT) to access OneNote through your MCP server.

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

## API Endpoints

- `GET /` - Health check
- `POST /v1/search` - Search OneNote content
- `POST /v1/get_page` - Get page by ID
- `POST /v1/write_note` - Create new page
- `GET /v1/notebooks` - List notebooks

## Authentication

All endpoints (except health check) require Bearer token authentication:
```
Authorization: Bearer memex-dev-token-2025
```

## Current Status

This is currently running with **simulated responses** for testing. To connect to real OneNote MCP server:

1. Install MCP client dependencies
2. Update the `simulate_mcp_call` function with real MCP client code
3. Configure your MCP server path

## For ChatGPT Integration

Use the Custom GPT configuration provided in the conversation artifacts to give ChatGPT direct access to this API.

## Logs

Check `memex_relay.log` for detailed logging and debugging information.