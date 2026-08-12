# QueryNova

> AI-powered data analysis assistant that lets you interact with databases using natural language.

**QueryNova** is a full-stack AI data analysis application built with React, Flask, SQLite, and OpenRouter. Users can ask questions about an e-commerce database in natural language and receive SQL-backed answers, tables, charts, and database insights.

---

## 🚀 Features

* 🤖 Natural-language database queries
* 🧠 AI-powered SQL generation using OpenRouter
* 🔒 Read-only SQL query validation
* 🗄️ SQLite e-commerce database
* 📊 Interactive charts and data visualization
* 🔗 ER diagram generation
* 🔄 Flowchart generation
* 🧩 Database schema explorer
* 💬 Conversational AI interface
* 💾 Browser-based conversation history
* 🌙 Modern dark-themed UI
* ⚡ React + Vite frontend
* 🐍 Flask REST API backend
* ☁️ Separate Vercel deployment for frontend and backend
* 🔐 Secure backend-only API key handling

---

## 🛠️ Tech Stack

### Frontend

* React
* Vite
* Axios
* Recharts
* Mermaid
* React Markdown
* Lucide React
* CSS

### Backend

* Python
* Flask
* Flask-CORS
* SQLAlchemy
* Pandas
* Pydantic
* OpenAI SDK
* Python-dotenv

### AI

* OpenRouter API
* `openrouter/free` model routing

### Database

* SQLite

### Deployment

* Vercel
* GitHub

---

## 🏗️ Architecture

```text
                     QueryNova
                        │
                        ▼
                React + Vite Frontend
                        │
                    REST API
                        │
                        ▼
                   Flask Backend
                    /        \
                   /          \
                  ▼            ▼
             OpenRouter      SQLite
                  AI         Database
```

---

## 📁 Project Structure

```text
querynova-ai/
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── backend/
│   ├── api/
│   │   └── index.py
│   ├── agent/
│   ├── database/
│   ├── data/
│   │   └── ecommerce.db
│   ├── llm/
│   ├── tools/
│   ├── app.py
│   ├── config.py
│   └── requirements.txt
│
├── .env.example
├── .gitignore
└── README.md
```

---

## 🗄️ Database

QueryNova uses a bundled read-only SQLite database.

```text
backend/data/ecommerce.db
```

### Tables

```text
categories
customers
inventory
order_items
orders
payments
products
shipments
```

### Main Relationships

```text
categories
     │
     ▼
 products ──────► inventory
     │
     ▼
order_items ────► orders
                     │
             ┌───────┼────────┐
             ▼       ▼        ▼
         customers payments shipments
```

---

## 🤖 How It Works

A user asks a question such as:

```text
Show me the top 5 products by revenue this quarter.
```

QueryNova:

1. Understands the user's question.
2. Inspects the database schema when required.
3. Generates SQL using OpenRouter.
4. Validates the generated SQL.
5. Executes the read-only query.
6. Processes the result.
7. Generates a human-friendly response.
8. Displays the result as text, table, or chart when appropriate.

---

## 🔒 SQL Security

Only read-only queries are allowed.

Supported:

```sql
SELECT ...
```

```sql
WITH ...
SELECT ...
```

Operations such as the following are blocked:

```text
INSERT
UPDATE
DELETE
DROP
ALTER
CREATE
TRUNCATE
REPLACE
ATTACH
DETACH
```

Query limits are also applied:

```env
MAX_QUERY_ROWS=500
QUERY_TIMEOUT_SECONDS=10
```

---

## 💬 Conversation History

Conversation history is stored in the browser using `localStorage`.

This means history:

* Survives page refreshes
* Survives browser restarts
* Works on the same browser/device

However, it is not currently synchronized across different browsers or devices.

The SQLite database is **not used to store chat history**.

---

# ⚙️ Installation

## Prerequisites

Make sure you have:

* Python 3.11+
* Node.js
* npm
* Git
* OpenRouter API key

---

## 1. Clone the Repository

```bash
git clone https://github.com/Sforsuraj/querynova-ai.git
cd querynova-ai
```

---

## 2. Backend Setup

```bash
cd backend
```

Create a virtual environment.

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 3. Backend Environment Variables

Create:

```text
backend/.env
```

Add:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=openrouter/free
OPENROUTER_APP_NAME=QueryNova

OPENROUTER_SITE_URL=http://localhost:5173
FRONTEND_URL=http://localhost:5173

MAX_QUERY_ROWS=500
QUERY_TIMEOUT_SECONDS=10
LLM_TIMEOUT_SECONDS=12

DATABASE_URL=sqlite:///data/ecommerce.db
```

> Never commit your real `.env` file or API key to GitHub.

---

## 4. Start Backend

```bash
python app.py
```

Backend:

```text
http://localhost:5000
```

---

## 5. Frontend Setup

Open another terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Create:

```text
frontend/.env.local
```

Add:

```env
VITE_API_URL=http://localhost:5000
```

Start the frontend:

```bash
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

# ☁️ Vercel Deployment

QueryNova uses **two separate Vercel projects**.

```text
GitHub Repository
       │
       ├──────────────► Frontend Vercel
       │                React + Vite
       │
       └──────────────► Backend Vercel
                        Flask + Python
```

---

## 🎨 Frontend Vercel Configuration

Create a new Vercel project from the repository.

Set:

```text
Root Directory:
frontend
```

Build Command:

```bash
npm run build
```

Output Directory:

```text
dist
```

Environment variable:

```env
VITE_API_URL=https://your-backend.vercel.app
```

---

## 🐍 Backend Vercel Configuration

Create another Vercel project from the same repository.

Set:

```text
Root Directory:
backend
```

Vercel should detect the Python API through:

```text
api/index.py
```

Backend environment variables:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=openrouter/free
OPENROUTER_APP_NAME=QueryNova

OPENROUTER_SITE_URL=https://your-frontend.vercel.app
FRONTEND_URL=https://your-frontend.vercel.app

MAX_QUERY_ROWS=500
QUERY_TIMEOUT_SECONDS=10
LLM_TIMEOUT_SECONDS=12

DATABASE_URL=sqlite:///data/ecommerce.db
```

---

# 🔍 API Endpoints

### Health

```http
GET /api/health
```

Example:

```json
{
  "runtime": "vercel-python",
  "service": "QueryNova",
  "status": "ok"
}
```

### Database Health

```http
GET /api/database/health
```

Example:

```json
{
  "database": "available",
  "status": "ok",
  "table_count": 8
}
```

### Database Schema

```http
GET /api/schema
```

Returns:

* Tables
* Columns
* Data types
* Primary keys
* Foreign keys
* Relationships

### Chat

```http
POST /api/chat
```

Processes natural-language database questions.

---

# 🧪 Example Queries

Try asking:

```text
Show me all products.
```

```text
Which product has the highest price?
```

```text
Show me the top 5 products by revenue.
```

```text
Which customers have placed the most orders?
```

```text
Show me all tables in the database.
```

```text
Show me the schema of the orders table.
```

```text
Draw the ER diagram for this database.
```

```text
Create a chart showing revenue by product.
```

---

# 🔐 Security

QueryNova follows several security practices:

* OpenRouter API key is stored only on the backend.
* API keys are never exposed through `VITE_*` variables.
* `.env` files are excluded from Git.
* SQL queries are validated before execution.
* Destructive SQL operations are blocked.
* Query row limits are enforced.
* Query execution time is restricted.
* CORS is configured for the deployed frontend.

---

# ⚡ Performance

Response time can depend on:

* OpenRouter model availability
* AI reasoning time
* Number of tool calls
* Database query complexity
* Network latency

The application uses query and LLM timeouts to prevent requests from running indefinitely.

---

# 🔮 Future Improvements

* User authentication
* Cloud-based conversation history
* Cross-device synchronization
* PostgreSQL support
* CSV/Excel upload
* Multiple database connections
* Saved queries
* Query history
* Export results
* Advanced dashboards
* Streaming AI responses
* Role-based access control

---

# 📌 Project Status

| Component              | Status |
| ---------------------- | ------ |
| React Frontend         | ✅      |
| Flask Backend          | ✅      |
| OpenRouter Integration | ✅      |
| SQLite Database        | ✅      |
| AI SQL Generation      | ✅      |
| SQL Validation         | ✅      |
| Charts                 | ✅      |
| ER Diagrams            | ✅      |
| Flowcharts             | ✅      |
| Conversation History   | ✅      |
| Vercel Frontend        | ✅      |
| Vercel Backend         | ✅      |

---

# 👨‍💻 Author

**Suraj Sharma**

Built as an AI-powered data analytics project using modern full-stack and AI technologies.

---

## ⭐ QueryNova

> **Ask questions. Analyze data. Get insights.**
