
# Omni Copilot — Frontend Plan

A sleek, dark-themed AI assistant frontend wired directly to the FastAPI backend at `http://localhost:8000`. No mocks, no simulated delays — every action hits a real endpoint with proper loading states.

## Routes

- `/auth` — public login/signup gateway
- `/` — protected chat dashboard (redirects to `/auth` if no token)

A small auth guard reads the JWT from `localStorage` on mount and redirects accordingly. Logout clears the token and sends the user back to `/auth`.

## Screens

### 1. Authentication Gateway (`/auth`)
- Centered card on a subtle gradient background
- Shadcn **Tabs**: "Login" | "Sign Up"
- Username + Password inputs with show/hide toggle
- **Login** → `POST /api/token` as `application/x-www-form-urlencoded`, stores `access_token` in `localStorage`, navigates to `/`
- **Sign Up** → `POST /api/signup` as JSON, then auto-switches to Login tab with a success toast
- Submit button shows spinner while pending; failed requests trigger Sonner error toasts with the backend message

### 2. Dashboard (`/`)
Two-column full-height layout:

**Sidebar (left, ~280px)**
- "Omni Copilot" wordmark with a Sparkles icon
- **Local Knowledge Base** card:
  - Input for `directory_path` (placeholder `/Users/name/docs`)
  - "Sync Directory" button → `POST /api/ingest`
  - Spinner on the button while pending; success/error toast based on response
  - Last synced path shown as a subtle status line below
- Spacer
- **Logout** button pinned to the bottom (clears localStorage → `/auth`)

**Chat Area (right, fills remaining space)**
- Top bar with current section label
- **ScrollArea** message history, auto-scrolls to bottom on new messages
- Message bubbles:
  - User: right-aligned, primary-tinted bubble, Avatar with initial
  - Assistant: left-aligned, muted bubble, Sparkles avatar, **react-markdown** render with prose styling for code blocks, lists, headings
- Empty state: friendly intro card with example prompts
- "Omni Copilot is thinking…" indicator (animated dots) while awaiting `/api/chat`
- Bottom composer: auto-resizing textarea + Send icon button (Enter to send, Shift+Enter for newline). Disabled while a request is in flight.

## API layer
A tiny `src/lib/api.ts` module with `signup`, `login`, `chat`, `ingest` functions. Each reads the token from localStorage where needed, sets the right headers, and throws on non-2xx so callers can toast cleanly.

## Visual style
- Dark theme by default (slate/zinc neutrals + indigo accent)
- Rounded-2xl cards, soft borders, subtle shadows
- Lucide icons throughout (Sparkles, Send, FolderSync, LogOut, Loader2, Eye)
- Sonner Toaster mounted in the root layout

## Dependencies to add
- `react-markdown` + `remark-gfm` (GitHub-flavored markdown for chat responses)

## Cleanup
- Replace the placeholder in `src/routes/index.tsx` with the protected dashboard
- Add `src/routes/auth.tsx` for the gateway
- Mount `<Toaster />` in `__root.tsx`
