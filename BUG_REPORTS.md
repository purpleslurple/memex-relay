# Bug Reports - Memex Relay API

## 🐛 BUG-001: Custom GPT Page ID Confusion
**Date:** 2025-06-26  
**Severity:** Medium  
**Component:** OpenAPI Schema / User Experience  

### Description
Custom GPT users cannot intuitively retrieve page content because the `/v1/pages/{pageId}` endpoint expects OneNote page IDs (cryptic strings like `0-F4873BF54ECA028!12345`) but users naturally try to use page titles.

### Steps to Reproduce
1. Configure Custom GPT with current schema
2. Ask Custom GPT to "get content for [page title]"
3. Custom GPT calls `/v1/pages/The%20Page%20Title` 
4. API returns 400 "Invalid Entity ID specified"

### Expected Behavior
Custom GPT should either:
- Be guided to call list pages first to get proper IDs
- Have access to a page-by-title lookup endpoint
- Get clear error messages explaining the ID requirement

### Actual Behavior
Custom GPT guesses that page titles are valid page IDs, resulting in confusing "Invalid Entity ID" errors.

### Root Cause
Schema design issue - no clear workflow documented for discovering page IDs before retrieving content.

### Workaround
Manually instruct Custom GPT to "use the page ID" after it gets proper IDs from list operations.

### Proposed Solutions
**Option A (Quick Fix):** Enhance schema descriptions with workflow guidance  
**Option B (Robust):** Add `/v1/pages/search?title={title}` endpoint  
**Option C (Flexible):** Modify existing endpoint to accept either ID or title

### API Logs
```
2025-06-26 23:41:28,800 - httpx - INFO - HTTP Request: GET https://graph.microsoft.com/v1.0/me/onenote/pages/The%20Great%20Reversal:%20Why%20My%20%22Unemployable%22%20Humanities%20Daughter%20Just%20Won%20the%20Future/content "HTTP/1.1 400 Bad Request"
2025-06-26 23:41:28,806 - mcp_client - ERROR - Error getting page content: 400 - {"error":{"code":"20112","message":"Invalid Entity ID specified."}}
```

### Impact
- Poor user experience for Custom GPT interactions
- Requires manual intervention to guide GPT through proper workflow
- Blocks natural page content retrieval workflows

---

## 🐛 BUG-002: VDTP Auto-Save Not Triggering
**Date:** 2025-06-26  
**Severity:** Medium  
**Component:** Claude Memory System / VDTP  

### Description
The reactive auto-save system specified to trigger every 25 paragraphs is not executing automatically. Manual save commands work correctly.

### Steps to Reproduce
1. Start conversation session
2. Continue past 25 paragraphs (should auto-save at P75)
3. Continue past 50 paragraphs (should auto-save at P100)
4. No automatic saves triggered

### Expected Behavior
System should automatically save conversation state every 25 paragraphs to maintain memory continuity.

### Actual Behavior
Auto-save system remains silent. Only manual `save`, `archive`, and `backup` commands function.

### Root Cause
Unknown - reactive save system implementation may have a trigger condition bug.

### Workaround
Use manual save commands periodically to maintain memory state.

### Impact
- Risk of memory loss if session crashes unexpectedly
- Reduced reliability of conversation continuity system
- Manual intervention required for memory management

### Configuration Reference
From status.md:
```
"Auto-Save Status: REACTIVE - saves every 25 paragraphs + manual triggers (save/archive/backup)"
```

### Current Status
- ✅ Manual save commands: WORKING
- ✅ Memory loading: WORKING  
- ❌ Reactive auto-save: NOT TRIGGERING
- ✅ Paragraph numbering: WORKING (currently at P102)

---

## 🐛 BUG-003: Custom GPT Authentication Token Expiration
**Date:** 2025-06-28  
**Severity:** High  
**Component:** Custom GPT / OpenAI Platform Integration  

### Description
Custom GPT authentication with memex-relay API expires periodically (time-based), requiring manual reset of Bearer token configuration. This breaks the Multi-Agent Memory Bus automation and forces fallback to manual relay mode.

### Steps to Reproduce
1. Configure Custom GPT with Bearer token `memex-dev-token-2025`
2. Verify authentication working (G can call API endpoints)
3. Wait [time period - needs measurement]
4. G attempts API calls and receives "Not authenticated" errors
5. Manual reset of authentication required

### Expected Behavior
Once configured, Custom GPT authentication should persist indefinitely or until manually changed.

### Actual Behavior
Authentication expires automatically after time period, breaking Multi-Agent Memory Bus functionality.

### Evidence
- Yesterday: Reset authentication to `memex-dev-token-2025` - worked
- Today: Same error returned - "Not authenticated"
- Reset process fixes issue immediately

### Root Cause Analysis
Likely causes (in order of probability):
1. **OpenAI session timeouts** - Custom GPT platform clears auth tokens periodically
2. **ngrok tunnel changes** - If tunnel URL changes, auth context might be lost
3. **Platform security policies** - Automatic token clearing as security measure
4. **Schema update side effects** - Configuration changes might reset auth

### Impact
- **High:** Breaks automated Multi-Agent Memory Bus
- Forces fallback to manual relay: G → User → OneNote
- Reduces collaborative AI efficiency
- Requires regular maintenance intervention

### Workaround
"Working ugly" approach: Accept periodic manual resets as maintenance requirement. Multi-Agent Memory Bus still functions via manual relay when auth expires.

### Monitoring Needed
- Track reset frequency to identify pattern
- Document time intervals between failures
- Monitor correlation with ngrok tunnel changes
- Check for OpenAI platform update announcements

### Status
**LOGGED AND ACCEPTED** - Working ugly approach until pattern identified or alternative auth method found.

---

*Bug reports generated automatically from conversation debugging sessions*