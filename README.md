# DATA MINIONS

DATA MINIONS is a React/Vite and Flask AI data-analysis application. It uses OpenRouter only from backend code and queries a bundled, read-only SQLite e-commerce sample.

## Deployment

Deploy two Vercel projects from this repository:

- **Frontend**: root `frontend`, build `npm run build`, output `dist`.
- **Backend**: root `backend`; Vercel detects `api/index.py` and installs `backend/requirements.txt`.

Frontend environment:

```env
VITE_API_URL=https://querynova-backend.vercel.app
```

Set an origin only—no trailing slash and no `/api` suffix.

Backend environment:

```env
OPENROUTER_API_KEY=...               # Backend only
OPENROUTER_MODEL=openrouter/free
OPENROUTER_APP_NAME=DATA MINIONS
OPENROUTER_SITE_URL=https://your-data-minions-frontend.vercel.app
FRONTEND_URL=https://your-data-minions-frontend.vercel.app
MAX_QUERY_ROWS=500
QUERY_TIMEOUT_SECONDS=10
LLM_TIMEOUT_SECONDS=12
DATABASE_URL=sqlite:///data/ecommerce.db
```

`FRONTEND_URL` accepts a comma-separated allow-list. Use the exact deployed frontend origin, without a trailing slash.

## Database

`backend/data/ecommerce.db` is packaged with the backend Vercel function and is read-only demo data. It contains categories, customers, inventory, order_items, orders, payments, products, and shipments.

Test the backend after deployment:

- `GET /api/health`
- `GET /api/database/health`
- `GET /api/schema`

## Conversation history

The e-commerce SQLite database is never used for conversations. Vercel local files and in-memory serverless state are not durable, so the production frontend stores its conversation history in that browser's `localStorage` and sends the recent context with each `/api/chat` request. History survives refreshes and browser restarts on the same browser, but is not shared between browsers/devices and is cleared if site storage is cleared. Durable cross-device history requires a separately configured hosted datastore.

## Security

- Never expose `OPENROUTER_API_KEY` as a `VITE_*` value.
- `.env` files are ignored. Commit only `.env.example` placeholders.
- All database SQL is validated as a single read-only `SELECT` or `WITH` statement.
