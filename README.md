# QueryNova AI

Ask your data. Discover what's next.

QueryNova is deployed as two independent Vercel projects from the same GitHub repository: a React/Vite frontend and a Flask/Python API. The backend safely queries the bundled read-only e-commerce SQLite sample and uses OpenRouter only from server code.

## Deployment architecture

```text
Browser → querynova-frontend.vercel.app → querynova-backend.vercel.app/api/*
                                              ├─ OpenRouter
                                              └─ SQLite ecommerce.db (read-only sample)
```

## Project structure

```text
frontend/                 Independent Vite project
  vercel.json
backend/                  Independent Flask project
  api/index.py            Vercel function entry point
  api/[...path].py        Catch-all for /api/*
  requirements.txt
  vercel.json
  data/ecommerce.db       Read-only bundled demo data
```

## Frontend deployment — querynova-frontend

1. In Vercel, import `Sforsuraj/querynova-ai`.
2. Set **Root Directory** to `frontend`.
3. Use framework **Vite**, build command `npm run build`, output directory `dist`.
4. Add this environment variable before deployment:

```env
VITE_API_URL=https://querynova-backend.vercel.app
```

5. Deploy and open `https://querynova-frontend.vercel.app`.

## Backend deployment — querynova-backend

1. Import the same repository into a second Vercel project.
2. Set **Root Directory** to `backend`.
3. Do not set a build command or run Flask/Gunicorn. Vercel detects `api/index.py` as a Python function and `api/[...path].py` handles `/api/*`.
4. Add these environment variables:

```env
OPENROUTER_API_KEY   (set this only in the Vercel dashboard)
OPENROUTER_MODEL=openrouter/free
OPENROUTER_APP_NAME=QueryNova AI
OPENROUTER_SITE_URL=https://querynova-frontend.vercel.app
FRONTEND_URL=https://your-frontend-production-domain.vercel.app
MAX_QUERY_ROWS=500
QUERY_TIMEOUT_SECONDS=10
DATABASE_URL=sqlite:///data/ecommerce.db
```

5. Deploy and test `https://querynova-backend.vercel.app/api/health`.

Expected response:

```json
{"status":"ok","service":"QueryNova AI","runtime":"vercel-python"}
```

## Local development

Backend:

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL=http://localhost:8080` locally. In Vercel, set `VITE_API_URL` to the backend origin only (for example `https://querynova-backend.vercel.app`): never append `/api` or a trailing slash. The backend CORS allow-list is configured by `FRONTEND_URL`; set it to the exact deployed frontend origin without a trailing slash. Multiple approved origins can be comma-separated.

## Security and limitations

- Never add `OPENROUTER_API_KEY` or any `VITE_OPENROUTER_API_KEY` to the frontend.
- `.env` files are ignored; `.env.example` contains placeholders only.
- The demo database is committed at `backend/data/ecommerce.db` and packaged with the backend function. It is read-only sample data; Vercel's serverless filesystem must not be used for persistent data.
- Conversation history uses an in-memory store on Vercel so the API remains available, but it is cleared when the function instance is recycled. Durable production history requires an external persistent data store.
- SQL is limited to a single read-only `SELECT` or `WITH` statement.

## API

- `GET /api/health`, `GET /api/database/health`, `GET /api/schema`
- `POST /api/chat`, `/api/query`, `/api/chart`, `/api/flowchart`
- `GET|POST /api/conversations`
- `GET|PUT|DELETE /api/conversations/:id`
- `POST /api/conversations/:id/messages`
