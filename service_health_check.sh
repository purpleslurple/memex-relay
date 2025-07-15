#!/bin/bash

# Service Health Check Script for Memex Relay System
# 
# HOW TO RUN:
# 1. Make executable: chmod +x service_health_check.sh
# 2. Run: ./service_health_check.sh
# 3. Or run from anywhere: ~/Desktop/memex-relay/service_health_check.sh
#
# WHAT IT CHECKS:
# - ngrok tunnel status and public URL
# - Memex Relay API health endpoint
# - OneNote authentication status
# - Quick endpoint functionality test
#
# PREREQUISITES:
# - ngrok running on port 4040
# - Memex Relay API running on port 5000
# - Valid authentication token (memex-dev-token-2025)

echo "🔍 Service Health Check - $(date)"
echo "================================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check ngrok tunnel
echo -n "🌐 ngrok tunnel: "
NGROK_STATUS=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null)
if [[ $? -eq 0 && $(echo "$NGROK_STATUS" | grep -c "public_url") -gt 0 ]]; then
    NGROK_URL=$(echo "$NGROK_STATUS" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['tunnels'][0]['public_url'] if data['tunnels'] else 'None')" 2>/dev/null)
    echo -e "${GREEN}✅ UP${NC} - $NGROK_URL"
else
    echo -e "${RED}❌ DOWN${NC}"
fi

# Check Memex Relay API with detailed status
echo -n "🚀 Memex Relay API: "
API_HEALTH=$(curl -s http://127.0.0.1:5000/ 2>/dev/null)
CURL_EXIT=$?

if [[ $CURL_EXIT -eq 0 && -n "$API_HEALTH" ]]; then
    # Try to parse the JSON response
    API_STATUS=$(echo "$API_HEALTH" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'service' in data and 'Memex Relay' in data.get('service', ''):
        print(f\"{data.get('status', 'unknown')}|{data.get('onenote_connectivity', 'unknown')}\")
    else:
        print('not_api|unknown')
except:
    print('parse_error|unknown')
" 2>/dev/null)
    
    STATUS=$(echo "$API_STATUS" | cut -d'|' -f1)
    ONENOTE=$(echo "$API_STATUS" | cut -d'|' -f2)
    
    if [[ "$STATUS" == "operational" ]]; then
        echo -e "${GREEN}✅ UP${NC} - OneNote: $ONENOTE"
    elif [[ "$STATUS" == "degraded" ]]; then
        echo -e "${YELLOW}⚠️  DEGRADED${NC} - OneNote: $ONENOTE"
    elif [[ "$STATUS" == "not_api" ]]; then
        echo -e "${RED}❌ DOWN${NC} - Got non-API response (ngrok error page?)"
    elif [[ "$STATUS" == "parse_error" ]]; then
        echo -e "${RED}❌ DOWN${NC} - Invalid JSON response"
    else
        echo -e "${RED}❌ ERROR${NC} - Status: $STATUS"
    fi
else
    echo -e "${RED}❌ DOWN${NC} - No response from localhost:5000"
fi

# Check OneNote Authentication
# Commented out - using /v1/notebooks endpoint test instead
# echo -n "📝 OneNote Auth: "
# AUTH_STATUS=$(curl -s -H "Authorization: Bearer memex-dev-token-2025" http://127.0.0.1:5000/v1/auth/status 2>/dev/null)
# if [[ $? -eq 0 ]]; then
#     AUTH_RESULT=$(echo "$AUTH_STATUS" | python3 -c "
# import sys, json
# try:
#     data = json.load(sys.stdin)
#     if data.get('authenticated'):
#         print('✅ AUTHENTICATED')
#     else:
#         print('❌ NOT AUTHENTICATED')
# except:
#     print('❓ UNKNOWN')
# " 2>/dev/null)
#     
#     if [[ "$AUTH_RESULT" == *"AUTHENTICATED"* ]]; then
#         echo -e "${GREEN}$AUTH_RESULT${NC}"
#     else
#         echo -e "${RED}$AUTH_RESULT${NC}"
#     fi
# else
#     echo -e "${RED}❌ API UNREACHABLE${NC}"
# fi

# Quick endpoint test with error details
echo ""
echo "🧪 OneNote Functionality Test:"
echo -n "   /v1/auth/status: "
AUTH_TEST=$(curl -s -H "Authorization: Bearer memex-dev-token-2025" http://127.0.0.1:5000/v1/auth/status 2>/dev/null)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer memex-dev-token-2025" http://127.0.0.1:5000/v1/auth/status 2>/dev/null)

if [[ "$HTTP_CODE" == "200" ]]; then
    AUTH_STATUS=$(echo "$AUTH_TEST" | python3 -c "import sys, json; data=json.load(sys.stdin); print('authenticated' if data.get('status') == 'authenticated' else 'not_authenticated')" 2>/dev/null || echo "unknown")
    if [[ "$AUTH_STATUS" == "authenticated" ]]; then
        USER_EMAIL=$(echo "$AUTH_TEST" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('email', 'unknown'))" 2>/dev/null || echo "unknown")
        echo -e "${GREEN}✅ AUTHENTICATED${NC} - $USER_EMAIL"
    else
        echo -e "${RED}❌ NOT AUTHENTICATED${NC}"
    fi
elif [[ "$HTTP_CODE" == "500" ]]; then
    ERROR_MSG=$(echo "$AUTH_TEST" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('detail', 'Unknown error'))" 2>/dev/null || echo "Internal server error")
    echo -e "${RED}❌ AUTH ERROR${NC} - $ERROR_MSG"
else
    echo -e "${RED}❌ FAILED${NC} - HTTP $HTTP_CODE"
fi

echo ""
echo "================================================"
echo "💡 Quick Commands:"
echo "   Start ngrok: ngrok http 5000"
echo "   Start API: cd ~/Desktop/memex-relay && python main.py"
echo "   Test notebooks: curl -H 'Authorization: Bearer memex-dev-token-2025' http://127.0.0.1:5000/v1/notebooks"