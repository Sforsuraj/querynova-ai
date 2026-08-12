import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import ReactMarkdown from "react-markdown";
import mermaid from "mermaid";
import {
  Sparkles,
  Plus,
  Send,
  Settings,
  ChevronDown,
  Copy,
  Check,
  Menu,
  Table2,
  Network,
  Search,
  AlertTriangle,
  Clock3,
  BarChart3,
  MoreHorizontal,
  RotateCcw,
  Download,
  Database,
} from "lucide-react";
import ChartRenderer from "./components/ChartRenderer";
import { api, apiUrl } from "./api/client";
import { conversationApi } from "./services/conversationStore";
import "./style.css";

const prompts = [
  [
    "Sales performance",
    "Show me the top 5 products by revenue this quarter.",
    BarChart3,
  ],
  ["Top customers", "Which customers have spent the most?", Search],
  ["Explore database", "Draw me the ER diagram for this database.", Network],
  ["Revenue trends", "Show monthly revenue for this year.", BarChart3],
];

const format = (k, v) => {
  if (v == null) return "—";
  if (typeof v !== "number") return String(v);
  if (/(revenue|spent|amount|price|total)/i.test(k))
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 2,
    }).format(v);
  if (/percent|rate|share/i.test(k) && v >= 0 && v <= 1)
    return new Intl.NumberFormat("en-US", {
      style: "percent",
      maximumFractionDigits: 1,
    }).format(v);
  return new Intl.NumberFormat("en-US", {
    notation: Math.abs(v) >= 1000000 ? "compact" : "standard",
    maximumFractionDigits: 2,
  }).format(v);
};

const normalize = (m) => ({
  ...m,
  queryResult: m.queryResult ?? m.query_result ?? null,
  toolCalls: m.toolCalls ?? m.tool_calls ?? [],
  sql: m.sql || null,
});

function ResultTable({ result }) {
  if (!result?.rows?.length) return null;
  const cols = result.columns || Object.keys(result.rows[0]);
  const download = () => {
    const text = [
      cols.join(","),
      ...result.rows.map((r) =>
        cols.map((c) => JSON.stringify(r[c] ?? "")).join(",")
      ),
    ].join("\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([text], { type: "text/csv" }));
    a.download = "querynova-results.csv";
    a.click();
    URL.revokeObjectURL(a.href);
  };
  return (
    <section className="result-card">
      <div className="card-top">
        <div>
          <Table2 size={16} />
          <b>Query results</b>
          <span>{result.row_count} rows</span>
        </div>
        <button className="text-action" onClick={download}>
          <Download size={14} /> CSV
        </button>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>#</th>
              {cols.map((c) => (
                <th key={c}>{c.replaceAll("_", " ")}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {result.rows.map((r, i) => (
              <tr key={i}>
                <td>{i + 1}</td>
                {cols.map((c) => (
                  <td key={c}>{format(c, r[c])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Diagram({ diagram }) {
  const ref = useRef();
  useEffect(() => {
    if (diagram && diagram.code) {
      mermaid
        .render(`querynova-${crypto.randomUUID()}`, diagram.code)
        .then((x) => ref.current && (ref.current.innerHTML = x.svg))
        .catch(() => ref.current && (ref.current.textContent = diagram.code));
    }
  }, [diagram]);
  return (
    diagram && (
      <section className="diagram-card">
        <div className="card-top">
          <div>
            <Network size={16} />
            <b>{diagram.type === "er" ? "Entity-Relationship Map" : "Process Flow"}</b>
          </div>
        </div>
        <div ref={ref} />
      </section>
    )
  );
}

function SQL({ sql }) {
  const [copied, setCopied] = useState(false);
  if (!sql) return null;
  return (
    <details className="sql">
      <summary>
        <ChevronDown size={16} /> Generated SQL
      </summary>
      <div className="sql-body">
        <button
          onClick={() =>
            navigator.clipboard?.writeText(sql).then(() => {
              setCopied(true);
              setTimeout(() => setCopied(false), 2000);
            })
          }
        >
          {copied ? <Check size={14} /> : <Copy size={14} />} {copied ? "Copied" : "Copy"}
        </button>
        <pre>{sql}</pre>
        <small>
          <Check size={13} /> Verified read-only query
        </small>
      </div>
    </details>
  );
}

function Insights({ data }) {
  if (!data?.key_insights?.length) return null;
  return (
    <section className="insights">
      <h3>
        <Sparkles size={16} /> Key insights
      </h3>
      <div>
        {data.key_insights.map((x, i) => (
          <article key={i}>
            <span>{i ? "✦" : "↑"}</span>
            <p>{x}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function Message({ m, retry, regenerate }) {
  if (m.role === "user") {
    return (
      <article className="message user">
        <div className="user-label">You</div>
        <div className="user-bubble">{m.content}</div>
      </article>
    );
  }

  if (m.failed) {
    return (
      <article className="message ai">
        <div className="ai-label">
          <span>✦</span> QueryNova
        </div>
        <div className="error">
          <AlertTriangle />
          <div>
            <b>QueryNova Error</b>
            <p>{m.content}</p>
            {m.errorDetails && <small className="muted">{m.errorDetails}</small>}
            {retry && (
              <button onClick={() => retry(m)} style={{ marginTop: "8px" }}>
                <RotateCcw size={14} /> Retry
              </button>
            )}
          </div>
        </div>
      </article>
    );
  }

  return (
    <article className="message ai">
      <div className="ai-label">
        <span>✦</span> QueryNova
      </div>
      <div className="answer">
        <ReactMarkdown>{m.content}</ReactMarkdown>
        <ResultTable result={m.queryResult} />
        <ChartRenderer
          visualization={m.visualization}
          onRemove={() => {}}
          onPin={() => {}}
        />
        <Diagram diagram={m.diagram} />
        <Insights data={m.insights} />
        <SQL sql={m.sql} />
        <div className="response-actions">
          <button onClick={() => navigator.clipboard?.writeText(m.content)}>
            <Copy size={14} /> Copy
          </button>
          <button onClick={() => regenerate(m)}>
            <RotateCcw size={14} /> Regenerate
          </button>
        </div>
      </div>
    </article>
  );
}

function Explorer() {
  const [schema, setSchema] = useState(null);
  const [openTable, setOpenTable] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get(apiUrl("/api/schema"))
      .then((res) => {
        setSchema(res.data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load database schema:", err);
        setLoading(false);
      });
  }, []);

  return (
    <section className="explorer">
      <p>DATABASE SCHEMA</p>
      {loading ? (
        <span className="muted">Loading schema…</span>
      ) : schema?.tables ? (
        Object.entries(schema.tables).map(([tableName, tableData]) => (
          <div key={tableName}>
            <button onClick={() => setOpenTable(openTable === tableName ? null : tableName)}>
              <ChevronDown size={14} />
              {tableName}
            </button>
            {openTable === tableName && (
              <ul>
                {Object.entries(tableData.columns).map(([colName, colType]) => (
                  <li key={colName}>
                    <span>{colName}</span>
                    <em>{colType}</em>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))
      ) : (
        <span className="muted">Schema unavailable</span>
      )}
    </section>
  );
}

function groups(items) {
  const t = new Date();
  t.setHours(0, 0, 0, 0);
  const y = new Date(t);
  y.setDate(t.getDate() - 1);
  const w = new Date(t);
  w.setDate(t.getDate() - 7);
  const out = { Today: [], Yesterday: [], "Previous 7 days": [], Older: [] };
  items.forEach((c) => {
    const d = new Date(c.updatedAt || c.createdAt);
    out[
      d >= t
        ? "Today"
        : d >= y
          ? "Yesterday"
          : d >= w
            ? "Previous 7 days"
            : "Older"
    ].push(c);
  });
  return out;
}

function App() {
  const [conversations, setConversations] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState("");
  const [mobile, setMobile] = useState(false);
  const [search, setSearch] = useState("");
  const [health, setHealth] = useState({ loading: true, ok: false, tables: 0 });

  const active = conversations.find((c) => c.id === activeId);

  const updateConversationState = (id, patch) =>
    setConversations((all) =>
      all.map((c) => (c.id === id ? { ...c, ...patch } : c))
    );

  async function select(id) {
    setActiveId(id);
    setMobile(false);
    setNotice("");
    try {
      const c = await conversationApi.get(id);
      updateConversationState(id, { ...c, messages: (c.messages || []).map(normalize) });
    } catch {
      setNotice("Couldn’t load this conversation.");
    }
  }

  async function newChat() {
    if (loading) return;
    try {
      const c = await conversationApi.create();
      setConversations((all) => [c, ...all.filter((x) => x.id !== c.id)]);
      setActiveId(c.id);
      setNotice("");
    } catch {
      setNotice("Unable to create a new conversation.");
    }
  }

  useEffect(() => {
    (async () => {
      try {
        const list = await conversationApi.list();
        setConversations(list);
        const saved = localStorage.getItem("querynova-active-conversation");
        const target = list.find((x) => x.id === saved) || list[0];
        if (target) {
          select(target.id);
        } else {
          newChat();
        }
      } catch {
        setNotice("Couldn’t load conversation history.");
      }
    })();

    setHealth({ loading: true, ok: false, tables: 0 });
    api
      .get(apiUrl("/api/database/health"))
      .then((r) => {
        const isOk = r.data.status === "ok" && r.data.database === "available";
        setHealth({
          loading: false,
          ok: isOk,
          tables: r.data.table_count || 8,
        });
      })
      .catch((err) => {
        console.error("Database health check error:", err);
        setHealth({ loading: false, ok: false, tables: 0 });
      });
  }, []);

  useEffect(() => {
    if (activeId) {
      localStorage.setItem("querynova-active-conversation", activeId);
    }
  }, [activeId]);

  async function send(text = input) {
    const messageText = text.trim();
    if (!messageText || loading || !active) return;

    setLoading(true);
    setNotice("");
    setInput("");

    try {
      const result = await conversationApi.send(active.id, messageText);
      const full = await conversationApi.get(active.id);
      updateConversationState(active.id, {
        title: full.title,
        updatedAt: full.updatedAt,
        messages: (full.messages || []).map(normalize),
      });

      if (result.error) {
        setNotice(result.error.message || "QueryNova AI request returned an error.");
      }
    } catch (err) {
      setNotice("The request could not be processed. Please check backend configuration.");
    } finally {
      setLoading(false);
    }
  }

  async function remove(id) {
    if (!confirm("Delete this conversation?")) return;
    try {
      await conversationApi.remove(id);
      const rest = conversations.filter((c) => c.id !== id);
      setConversations(rest);
      if (id === activeId) {
        rest[0] ? select(rest[0].id) : newChat();
      }
    } catch {
      setNotice("Unable to delete this conversation.");
    }
  }

  async function rename(c) {
    const title = prompt("Rename conversation", c.title);
    if (!title?.trim()) return;
    try {
      const saved = await conversationApi.rename(c.id, title);
      updateConversationState(c.id, saved);
    } catch {
      setNotice("Unable to rename this conversation.");
    }
  }

  const visibleConversations = conversations.filter((c) =>
    (c.title || "").toLowerCase().includes(search.toLowerCase())
  );

  const regenerate = async (m) => {
    if (loading || !active) return;
    setLoading(true);
    try {
      const r = await conversationApi.regenerate(active.id, m.id);
      updateConversationState(active.id, {
        messages: active.messages.map((x) =>
          x.id === m.id ? normalize(r.message) : x
        ),
      });
    } catch (err) {
      setNotice("Unable to regenerate this response.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main>
      <aside className={mobile ? "show" : ""}>
        <div className="brand">
          <span>✦</span> QueryNova
        </div>
        <button className="new" onClick={newChat} disabled={loading}>
          <Plus size={16} /> New chat
        </button>
        <div className="conversation-search">
          <Search size={14} />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search conversations…"
            aria-label="Search conversations"
          />
        </div>
        {Object.entries(groups(visibleConversations)).map(
          ([name, list]) =>
            list.length > 0 && (
              <section className="chat-list" key={name}>
                <p className="section">{name.toUpperCase()}</p>
                {list.map((c) => (
                  <div
                    className={c.id === activeId ? "active-chat" : "chat-row"}
                    key={c.id}
                  >
                    <button onClick={() => select(c.id)}>
                      <Clock3 size={14} />
                      <span>
                        <b>{c.title || "New chat"}</b>
                        <small>{c.preview}</small>
                      </span>
                    </button>
                    <details>
                      <summary aria-label="Conversation actions">
                        <MoreHorizontal size={15} />
                      </summary>
                      <div>
                        <button onClick={() => rename(c)}>Rename</button>
                        <button onClick={() => remove(c.id)}>Delete</button>
                      </div>
                    </details>
                  </div>
                ))}
              </section>
            )
        )}
        <Explorer />
        <div className="side-bottom">
          <div className="connection">
            <i className={health.loading ? "loading" : health.ok ? "" : "offline"} />
            <div>
              <b>SQLite Database</b>
              <span>
                {health.loading
                  ? "Checking health..."
                  : health.ok
                    ? `${health.tables} tables · Connected`
                    : "Database unavailable"}
              </span>
            </div>
          </div>
        </div>
      </aside>
      <section className="workspace">
        <header>
          <button
            className="menu"
            aria-label="Open navigation"
            onClick={() => setMobile(!mobile)}
          >
            <Menu />
          </button>
          <div className="header-brand">
            <span>✦</span>
            <b>QueryNova</b>
          </div>
          <div className={"connected " + (health.ok ? "" : "unavailable")}>
            <i />
            <span>
              {health.loading
                ? "Connecting..."
                : health.ok
                  ? "Connected"
                  : "Database unavailable"}
            </span>
            <b>{health.ok ? "SQLite" : ""}</b>
          </div>
        </header>
        <div className="conversation">
          {notice && (
            <div className="error">
              <AlertTriangle />
              <div>
                <b>Notice</b>
                <p>{notice}</p>
                <button onClick={() => activeId && select(activeId)}>
                  Refresh
                </button>
              </div>
            </div>
          )}
          {!active ? (
            <div className="loading">
              <Sparkles size={16} /> Loading conversation…
            </div>
          ) : !active.messages?.length ? (
            <div className="empty">
              <div className="nova">✦</div>
              <h1>QueryNova</h1>
              <p>Ask your data. Discover insights instantly.</p>
              <span className="landing-copy">
                Query Nova bridges natural language with SQLite databases.
              </span>
              <div className="prompt-cards">
                {prompts.map(([t, q, I]) => (
                  <button key={t} onClick={() => send(q)} disabled={loading}>
                    <I />
                    <b>{t}</b>
                    <span>{q}</span>
                  </button>
                ))}
              </div>
              <div className="quick">
                {[
                  "give me all product names",
                  "show me the top 5 products by revenue",
                  "give me the name of all tables present inside the database",
                  "draw the ER diagram",
                  "show revenue by product as a chart",
                ].map((q) => (
                  <button key={q} onClick={() => send(q)} disabled={loading}>
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            active.messages.map((m) => (
              <Message
                m={m}
                key={m.id}
                retry={() => send(m.content)}
                regenerate={regenerate}
              />
            ))
          )}
          {loading && (
            <div className="loading">
              <Sparkles size={16} />
              <div>
                <b>QueryNova is analyzing your request…</b>
                <span>
                  Understanding question · Querying SQLite database · Generating insights
                </span>
              </div>
            </div>
          )}
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            send();
          }}
        >
          <input
            aria-label="Ask your database"
            disabled={loading || !active}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything about your database…"
          />
          <button disabled={loading || !active || !input.trim()} aria-label="Send">
            <Send size={18} />
          </button>
        </form>
        <p className="disclaimer">
          QueryNova AI can make mistakes. Verify important financial or analytical results.
        </p>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
