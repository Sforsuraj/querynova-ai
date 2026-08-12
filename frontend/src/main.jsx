import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import axios from "axios";
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
} from "lucide-react";
import ChartRenderer from "./components/ChartRenderer";
import { conversationApi } from "./services/conversationStore";
import "./style.css";
const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? "http://localhost:8080" : "");
const API = `${API_URL}/api`;
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
  if (typeof v !== "number") return v;
  if (/(revenue|spent|amount|price|total)/i.test(k))
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
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
  let cols = result.columns || Object.keys(result.rows[0]),
    download = () => {
      let text = [
          cols.join(","),
          ...result.rows.map((r) =>
            cols.map((c) => JSON.stringify(r[c] ?? "")).join(","),
          ),
        ].join("\n"),
        a = document.createElement("a");
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
  let ref = useRef();
  useEffect(() => {
    if (diagram)
      mermaid
        .render(`nova-${crypto.randomUUID()}`, diagram.code)
        .then((x) => ref.current && (ref.current.innerHTML = x.svg))
        .catch(() => ref.current && (ref.current.textContent = diagram.code));
  }, [diagram]);
  return (
    diagram && (
      <section className="diagram-card">
        <div className="card-top">
          <div>
            <Network size={16} />
            <b>{diagram.type === "er" ? "Database map" : "Process flow"}</b>
          </div>
        </div>
        <div ref={ref} />
      </section>
    )
  );
}
function SQL({ sql }) {
  let [c, setC] = useState(false);
  if (!sql) return null;
  return (
    <details className="sql">
      <summary>
        <ChevronDown size={16} /> Generated SQL
      </summary>
      <div className="sql-body">
        <button
          onClick={() =>
            navigator.clipboard?.writeText(sql).then(() => setC(true))
          }
        >
          {c ? <Check size={14} /> : <Copy size={14} />} {c ? "Copied" : "Copy"}
        </button>
        <pre>{sql}</pre>
        <small>
          <Check size={13} /> Read-only query
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
  if (m.role === "user")
    return (
      <article className="message user">
        <div className="user-label">You</div>
        <div className="user-bubble">{m.content}</div>
      </article>
    );
  if (m.failed)
    return (
      <article className="message ai">
        <div className="ai-label">
          <span>✦</span> QueryNova
        </div>
        <div className="error">
          <AlertTriangle />
          <div>
            <b>Something went wrong while generating the response.</b>
            <p>{m.content}</p>
            <button onClick={() => retry(m)}>
              <RotateCcw size={14} /> Retry
            </button>
          </div>
        </div>
      </article>
    );
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
  let [s, setS] = useState(null),
    [open, setOpen] = useState(null);
  useEffect(() => {
    axios
      .get(API + "/schema")
      .then((x) => setS(x.data))
      .catch(() => {});
  }, []);
  return (
    <section className="explorer">
      <p>DATABASE</p>
      {s ? (
        Object.entries(s.tables).map(([n, t]) => (
          <div key={n}>
            <button onClick={() => setOpen(open === n ? null : n)}>
              <ChevronDown size={14} />
              {n}
            </button>
            {open === n && (
              <ul>
                {Object.entries(t.columns).map(([k, v]) => (
                  <li key={k}>
                    <span>{k}</span>
                    <em>{v}</em>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))
      ) : (
        <span className="muted">Loading schema…</span>
      )}
    </section>
  );
}
function groups(items) {
  let t = new Date();
  t.setHours(0, 0, 0, 0);
  let y = new Date(t);
  y.setDate(t.getDate() - 1);
  let w = new Date(t);
  w.setDate(t.getDate() - 7);
  let out = { Today: [], Yesterday: [], "Previous 7 days": [], Older: [] };
  items.forEach((c) => {
    let d = new Date(c.updatedAt);
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
  let [conversations, setConversations] = useState([]),
    [activeId, setActiveId] = useState(null),
    [input, setInput] = useState(""),
    [loading, setLoading] = useState(false),
    [notice, setNotice] = useState(""),
    [mobile, setMobile] = useState(false),
    [search, setSearch] = useState(""),
    [health, setHealth] = useState({ ok: false, tables: 0 });
  let active = conversations.find((c) => c.id === activeId);
  let change = (id, patch) =>
    setConversations((all) =>
      all.map((c) => (c.id === id ? { ...c, ...patch } : c)),
    );
  async function select(id) {
    setActiveId(id);
    setMobile(false);
    setNotice("");
    try {
      let c = await conversationApi.get(id);
      change(id, { ...c, messages: c.messages.map(normalize) });
    } catch {
      setNotice("Couldn’t load this conversation.");
    }
  }
  async function newChat() {
    if (loading) return;
    try {
      let c = await conversationApi.create();
      setConversations((all) => [c, ...all]);
      setActiveId(c.id);
      setNotice("");
    } catch {
      setNotice("Unable to create a new conversation.");
    }
  }
  useEffect(() => {
    (async () => {
      try {
        let list = await conversationApi.list();
        setConversations(list);
        let saved = localStorage.getItem("querynova_active_conversation");
        let target = list.find((x) => x.id === saved) || list[0];
        if (target) select(target.id);
        else newChat();
      } catch {
        setNotice("Couldn’t load conversations.");
      }
    })();
    axios
      .get(API + "/database/health")
      .then((r) =>
        setHealth({
          ok: r.data.database === "available",
          tables: r.data.table_count || 0,
        }),
      )
      .catch(() => setHealth({ ok: false, tables: 0 }));
  }, []);
  useEffect(() => {
    if (activeId)
      localStorage.setItem("querynova_active_conversation", activeId);
  }, [activeId]);
  async function send(text = input, failedId) {
    if (!text.trim() || loading || !active) return;
    let snapshot = active.messages || [];
    setLoading(true);
    setNotice("");
    if (failedId)
      change(active.id, {
        messages: snapshot.filter((m) => m.id !== failedId),
      });
    else
      change(active.id, {
        messages: [
          ...snapshot,
          { id: `pending-${crypto.randomUUID()}`, role: "user", content: text },
        ],
      });
    setInput("");
    try {
      let r = await conversationApi.send(active.id, text),
        u = normalize(r.user_message),
        a = normalize(r.message),
        full = await conversationApi.get(active.id);
      change(active.id, {
        title: full.title,
        updatedAt: a.timestamp,
        messages: [...snapshot.filter((m) => !m.failed), u, a],
      });
    } catch {
      change(active.id, {
        messages: [
          ...snapshot.filter((m) => !m.id.startsWith("pending-")),
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content: "Your user message remains saved. Please try again.",
            failed: true,
            source: text,
          },
        ],
      });
      setNotice("Unable to save the assistant response.");
    } finally {
      setLoading(false);
    }
  }
  async function remove(id) {
    if (!confirm("Delete this conversation?")) return;
    try {
      await conversationApi.remove(id);
      let rest = conversations.filter((c) => c.id !== id);
      setConversations(rest);
      id === activeId && (rest[0] ? select(rest[0].id) : newChat());
    } catch {
      setNotice("Unable to delete this conversation.");
    }
  }
  async function rename(c) {
    let title = prompt("Rename conversation", c.title);
    if (!title?.trim()) return;
    try {
      let saved = await conversationApi.rename(c.id, title);
      change(c.id, saved);
    } catch {
      setNotice("Unable to rename this conversation.");
    }
  }
  let visible = conversations.filter((c) =>
    c.title.toLowerCase().includes(search.toLowerCase()),
  );
  let regenerate = async (m) => {
    if (loading || !active) return;
    setLoading(true);
    try {
      let r = await conversationApi.regenerate(active.id, m.id);
      change(active.id, {
        messages: active.messages.map((x) =>
          x.id === m.id ? normalize(r.message) : x,
        ),
      });
    } catch {
      setNotice("Unable to regenerate this response.");
    } finally {
      setLoading(false);
    }
  };
  return (
    <main>
      <aside className={mobile ? "show" : ""}>
        <div className="brand">
          <span>✦</span> QueryNova <b>AI</b>
        </div>
        <button className="new" onClick={newChat}>
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
        {Object.entries(groups(visible)).map(
          ([name, list]) =>
            list.length && (
              <section className="chat-list" key={name}>
                <p className="section">{name.toUpperCase()}</p>
                {list.map((c) => (
                  <div
                    className={c.id === activeId ? "active-chat" : "chat-row"}
                    key={c.id}
                  >
                    <button onClick={() => select(c.id)}>
                      <Clock3 size={14} />
                      <span>{c.title}</span>
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
            ),
        )}
        <Explorer />
        <div className="side-bottom">
          <div className="connection">
            <i className={health.ok ? "" : "offline"} />
            <div>
              <b>SQLite</b>
              <span>
                {health.ok
                  ? `${health.tables} tables · Connected`
                  : "Database unavailable"}
              </span>
            </div>
          </div>
          <button>
            <Settings size={15} /> Settings
          </button>
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
            <b>QueryNova AI</b>
          </div>
          <div className={"connected " + (health.ok ? "" : "unavailable")}>
            <i />
            <span>{health.ok ? "Connected" : "Database unavailable"}</span>
            <b>{health.ok ? "SQLite" : ""}</b>
          </div>
        </header>
        <div className="conversation">
          {notice && (
            <div className="error">
              <AlertTriangle />
              <div>
                <b>Conversation notice</b>
                <p>{notice}</p>
                <button onClick={() => activeId && select(activeId)}>
                  Retry
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
              <h1>QueryNova AI</h1>
              <p>Ask your data. Discover what’s next.</p>
              <span className="landing-copy">
                Your database has answers. You just need to ask.
              </span>
              <div className="prompt-cards">
                {prompts.map(([t, q, I]) => (
                  <button key={t} onClick={() => send(q)}>
                    <I />
                    <b>{t}</b>
                    <span>{q}</span>
                  </button>
                ))}
              </div>
              <div className="quick">
                {[
                  "Which products have never been ordered?",
                  "Show monthly revenue for this year",
                  "Draw the ER diagram for this database",
                ].map((q) => (
                  <button key={q} onClick={() => send(q)}>
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
                retry={(x) => send(x.source, x.id)}
                regenerate={regenerate}
              />
            ))
          )}
          {loading && (
            <div className="loading">
              <Sparkles size={16} />
              <div>
                <b>QueryNova is analyzing your data…</b>
                <span>
                  Understanding your question · Checking the database ·
                  Preparing insights
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
          <button disabled={loading || !active} aria-label="Send">
            <Send size={18} />
          </button>
        </form>
        <p className="disclaimer">
          QueryNova can make mistakes. Verify important results.
        </p>
      </section>
    </main>
  );
}
createRoot(document.getElementById("root")).render(<App />);
