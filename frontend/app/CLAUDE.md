<system_context>
Next.js App Router pages for the Reddit comments + Reddit/LinkedIn post repurposing tool.
Uses React 19 with client components for interactivity.
</system_context>

<file_map>
## FILE MAP
- `page.tsx` - Main single-page application with all UI logic
- `layout.tsx` - Root layout with metadata
- `globals.css` - All styles (no CSS modules)
</file_map>

<paved_path>
## ARCHITECTURE (PAVED PATH)

### State Management
- `isAuthenticated` / `passwordInput` / `authError` / `isAuthChecking` - Auth state
- `inputType` - "urls" or "keywords"
- `inputText` - Raw textarea content
- `taskId` - Current task being polled
- `status` - "running", "complete", "failed"
- `results` - Full TaskResults object
- `commentFilter` / `postFilter` - "all", "pass", "unsure", "fail"

### Component Structure
Single page.tsx contains:
1. Password screen (when not authenticated)
2. Header bar with logout button
3. History dropdown
4. Input section (radio + textarea + button)
5. Status bar with spinner
6. Results sections (3 sections with filtering)
   - Comments section shows "Why selected" reasoning
   - "Reddit and LinkedIn Suggestions" section shows "Why it scores well" reasoning + strategy paragraph

### API Integration
- `authFetch()` - Wraps fetch() with X-Access-Password header + auto-logout on 401
- `handleLogin()` - POST /auth/verify
- `handleRun()` - POST /run
- `pollStatus()` - GET /status/{task_id}
- `fetchResults()` - GET /results/{task_id}
- `fetchHistory()` - GET /history
</paved_path>

<critical_notes>
## CRITICAL NOTES
- **"use client"** - Required for useState/useEffect
- **API_BASE** - Uses NEXT_PUBLIC_API_BASE env var, falls back to localhost:8007
- **POLL_INTERVAL** - 5 seconds (5000ms)
- **Auth** - Password in sessionStorage, auto-verified on mount, auto-logout on 401
- **No external state library** - Plain React hooks only
</critical_notes>
