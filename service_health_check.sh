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

# Check Memex Relay API
echo -n "🚀 Memex Relay API: "
API_HEALTH=$(curl -s http://127.0.0.1:5000/ 2>/dev/null)
if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✅ UP${NC} - $(echo "$API_HEALTH" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "Response received")"
else
    echo -e "${RED}❌ DOWN${NC}"
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

# Quick endpoint test
echo ""
echo "🧪 Quick Endpoint Test:"
echo -n "   /v1/notebooks: "
NOTEBOOKS_TEST=$(curl -s -H "Authorization: Bearer memex-dev-token-2025" http://127.0.0.1:5000/v1/notebooks 2>/dev/null)
if [[ $? -eq 0 && $(echo "$NOTEBOOKS_TEST" | grep -c "notebooks\|error") -gt 0 ]]; then
    echo -e "${GREEN}✅ RESPONDING${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

echo ""
echo "================================================"
echo "💡 Quick Commands:"
echo "   Start ngrok: ngrok http 5000"
echo "   Start API: cd ~/Desktop/memex-relay && python main.py"
echo "   Test notebooks: curl -H 'Authorization: Bearer memex-dev-token-2025' http://127.0.0.1:5000/v1/notebooks"