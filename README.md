# QueryNova

> AI-powered e-commerce data analysis assistant that transforms natural language questions into safe, read-only SQL queries, interactive visualizations, and structured database insights.

**QueryNova** connects a modern React + Vite frontend on Vercel to a Flask backend on Vercel, powered strictly by OpenRouter AI and a read-only SQLite database.

---

## 🌐 Live Deployments

* **Frontend App**: [https://querynova-frontend.vercel.app](https://querynova-frontend.vercel.app)
* **Backend API**: [https://querynova-backend.vercel.app](https://querynova-backend.vercel.app)

---

## 🏗️ Architecture

```text
QueryNova Frontend (Vercel)
   │ (HTTPS / Axios)
   ▼
QueryNova Backend (Vercel Flask Serverless)
   ├── OpenRouter AI (openrouter/free) ──► SQL Query Generation & Insights
   └── SQLite Database (backend/data/ecommerce.db) ──► Read-Only Query Execution
```

* **Frontend**: React, Vite, Axios, Recharts, Mermaid, React Markdown, Lucide React.
* **Backend**: Python 3.11+, Flask, Flask-CORS, SQLAlchemy, Pandas, Pydantic, OpenAI SDK.
* **AI Provider**: OpenRouter (`openrouter/free`).
* **Database**: Packaged read-only SQLite database (`backend/data/ecommerce.db`).
* **Conversation History**: Stored locally in the user's browser using `localStorage` (`querynova-conversations-v1`).

---

## 🗄️ Database Schema

The bundled e-commerce SQLite database contains 8 tables:

1. `categories` (id, name, description)
2. `customers` (id, name, email, phone, city, state, country, created_at)
3. `inventory` (id, product_id, quantity, reorder_level, location, updated_at)
4. `order_items` (id, order_id, product_id, quantity, unit_price)
5. `orders` (id, customer_id, order_date, status, total_amount, shipping_address)
6. `payments` (id, order_id, payment_date, payment_method, amount, status)
7. `products` (id, category_id, name, description, price, sku, created_at)
8. `shipments` (id, order_id, tracking_number, carrier, status, shipped_date, estimated_delivery)

---

## 🔌 API Endpoints

### 1. Backend Health Check
```http
GET /api/health
```
Response:
```json
{
  "runtime": "vercel-python",
  "service": "QueryNova",
  "status": "ok"
}
```

### 2. Database Health Check
```http
GET /api/database/health
```
Response:
```json
{
  "database": "available",
  "status": "ok",
  "table_count": 8
}
```

### 3. Schema Metadata
```http
GET /api/schema
```
Returns all 8 tables, column data types, primary keys, and foreign key relationships.

### 4. Natural Language Chat & Analytics
```http
POST /api/chat
Content-Type: application/json

{
  "message": "show me the top 5 products by revenue",
  "conversation_id": "optional-uuid",
  "messages": []
}
```
Response:
```json
{
  "conversation_id": "...",
  "message": "Here are the top 5 products by revenue...",
  "sql": "SELECT p.name AS product, ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue FROM products p JOIN order_items oi ON oi.product_id = p.id GROUP BY p.id, p.name ORDER BY revenue DESC LIMIT 5",
  "query_result": { "success": true, "columns": ["product", "revenue"], "rows": [...], "row_count": 5 },
  "visualization": { "type": "bar", "title": "...", "data": [...] },
  "insights": { "summary": "...", "key_insights": [...] }
}
```

---

## 🔒 Security & SQL Safety

* **Strict Read-Only Enforcement**: Only `SELECT` and `WITH ... SELECT` queries are permitted.
* **Blocked Operations**: `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`, `REPLACE`, `ATTACH`, `DETACH`, `VACUUM`, `PRAGMA`, and multi-statement semicolon chaining are rejected by the SQL validator.
* **Secrets Protection**: `OPENROUTER_API_KEY` is kept strictly on the backend server. Frontend code only communicates with the backend API.
* **Resource Limits**: `MAX_QUERY_ROWS=500`, `QUERY_TIMEOUT_SECONDS=10`, `LLM_TIMEOUT_SECONDS=12`.

---

## ⚙️ Local Development Setup

### 1. Backend Setup

```bash
cd backend
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
```

Create `backend/.env`:
```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=openrouter/free
OPENROUTER_APP_NAME=QueryNova
OPENROUTER_SITE_URL=http://localhost:5173
FRONTEND_URL=http://localhost:5173
MAX_QUERY_ROWS=500
QUERY_TIMEOUT_SECONDS=10
LLM_TIMEOUT_SECONDS=12
DATABASE_URL=sqlite:///data/ecommerce.db
```

Start the Flask backend:
```bash
python app.py
```
Backend runs at `http://localhost:8080`.

### 2. Frontend Setup

In a new terminal:
```bash
cd frontend
npm install
```

Create `frontend/.env.local`:
```env
VITE_API_URL=http://localhost:8080
```

Start Vite dev server:
```bash
npm run dev
```
Frontend runs at `http://localhost:5173`.

---

## ☁️ Vercel Deployment Configuration

QueryNova is deployed as two separate Vercel projects from the same GitHub repository:

### 1. Frontend Vercel Project
* **Root Directory**: `frontend`
* **Framework Preset**: Vite
* **Build Command**: `npm run build`
* **Output Directory**: `dist`
* **Environment Variables**:
  `VITE_API_URL=https://querynova-backend.vercel.app`

### 2. Backend Vercel Project
* **Root Directory**: `backend`
* **Entrypoint**: `api/index.py`
* **Environment Variables**:
  * `OPENROUTER_API_KEY`: your-openrouter-key
  * `OPENROUTER_MODEL`: `openrouter/free`
  * `OPENROUTER_APP_NAME`: `QueryNova`
  * `OPENROUTER_SITE_URL`: `https://querynova-frontend.vercel.app`
  * `FRONTEND_URL`: `https://querynova-frontend.vercel.app`
  * `MAX_QUERY_ROWS`: `500`
  * `QUERY_TIMEOUT_SECONDS`: `10`
  * `LLM_TIMEOUT_SECONDS`: `12`

---

## 🧪 Testing

Run backend tests:
```bash
pytest backend/
```

Test frontend build:
```bash
cd frontend && npm run build
```
