# QueryNova AI

**Ask your data. Discover what's next.**

QueryNova AI is a conversational analytics workspace for the bundled e-commerce sample database. It combines a React/Vite interface with a Flask AI agent, safe read-only SQL, charts, SQL transparency, ER diagrams, flowcharts, and conversation history.

## Architecture

```text
User → Vercel
       ├─ React + Vite frontend (/)
       └─ Flask API (/api)
            ├─ QueryNova agent → OpenRouter → LLM
            └─ SQLite sample database
```

The browser calls the same deployment with relative `/api` paths. OpenRouter credentials are used only by the Python function.

## Features

- Persistent conversation UI, search, rename, delete, and regeneration
- Safe `SELECT`/`WITH` SQL only
- Grounded agent tool calls: schema, query, chart, diagram, and insight tools
- Bar, line, pie, and scatter charts attached to each response
- Mermaid ER diagrams and order-flow diagrams
- Collapsible SQL, CSV export, result tables, and connection health endpoint

## Project structure

```text
api/index.py                 Vercel Python/Flask entry point
backend/                     Flask application, agent, tools, SQLite database
frontend/                    React/Vite client
vercel.json                  Vercel build and /api routing
requirements.txt             Python dependencies for Vercel
```

## Environment variables

Copy `.env.example` to `.env` for local development. Never commit `.env` or put secrets in the client.

| Variable | Required | Purpose |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | Yes | Server-side OpenRouter credential |
| `OPENROUTER_MODEL` | Yes | Model/router, e.g. `openrouter/free` |
| `OPENROUTER_APP_NAME` | Yes | Application attribution |
| `OPENROUTER_SITE_URL` | Optional | Final Vercel URL |
| `DATABASE_URL` | Yes | `sqlite:///database/ecommerce.db` for demo |
| `MAX_QUERY_ROWS` | Yes | Read-only query result limit |
| `QUERY_TIMEOUT_SECONDS` | Yes | Query timeout setting |
| `VITE_API_URL` | Build-time | `/api` in production |

For local Vite development, use `VITE_API_URL=http://localhost:8080/api` and `FRONTEND_URL=http://localhost:5173`.

## Local setup

```bash
pip install -r requirements.txt
python -m backend.app
```

In a second terminal:

```bash
cd frontend
pnpm install
pnpm run dev
```

Open `http://localhost:5173`. To test the same routing topology locally, install the Vercel CLI and run `vercel dev` at the repository root.

## Vercel deployment

1. Push this repository to GitHub.
2. In Vercel, import the GitHub repository with the **repository root** as the project root.
3. Vercel uses `vercel.json` to install/build `frontend`, publish `frontend/dist`, and route `/api/*` to `api/index.py`.
4. In **Settings → Environment Variables**, add the required variables listed above. Set `VITE_API_URL=/api`.
5. Optionally set `OPENROUTER_SITE_URL` to your deployed `https://…vercel.app` URL.
6. Deploy, then open `https://YOUR-PROJECT.vercel.app/api/health`.
7. Test a ranking prompt and `Draw me the ER diagram for this database.`

No separate backend host is required: the static client and Flask API run from one Vercel project.

## API

- `GET /api/health` — lightweight backend/database status
- `GET /api/schema` — cached database schema
- `POST /api/chat`, `POST /api/query`, `POST /api/chart`, `POST /api/flowchart`
- `GET|POST /api/conversations`
- `GET|PUT|DELETE /api/conversations/:id`
- `POST /api/conversations/:id/messages`
- `POST /api/conversations/:id/messages/:messageId/regenerate`

## Database and serverless limitations

`ecommerce.db` is packaged as a **read-only sample database** for the hackathon demo. SQLite paths are resolved relative to the deployed project, not a machine-specific directory.

Vercel functions are stateless and their writable filesystem is not durable. Conversation history uses `/tmp` on Vercel only as a best-effort warm-function demo store; it is not reliable persistent storage. For production chat history, replace it with a hosted database such as PostgreSQL. Do not rely on in-memory state, background processes, or self-pinging.

## Security

- Keep `OPENROUTER_API_KEY` in Vercel server environment variables only.
- The frontend never receives provider secrets.
- SQL is restricted to a single read-only `SELECT` or `WITH` query.
- Database results, chart values, and diagrams are generated from actual tool output.

## Hackathon demo

1. Ask: `Show me the top 5 products by revenue this quarter.`
2. Open the chart and generated SQL.
3. Ask: `Now show their trend over the last year.`
4. Ask for the ER diagram.
5. Create a new chat and switch back to demonstrate isolated history.

## Troubleshooting

- `/api/health` failing: check Python dependency installation and database path settings.
- AI request unavailable: confirm the OpenRouter key and model are configured in Vercel.
- Lost history after a serverless cold start: expected with the demo SQLite history store; use a hosted database for durable history.
