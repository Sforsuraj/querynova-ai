import { api, apiUrl } from "../api/client";

const STORAGE_KEY = "querynova-conversations-v1";

const now = () => new Date().toISOString();

const createMessage = (role, content, extras = {}) => ({
  id: crypto.randomUUID(),
  role,
  content,
  timestamp: now(),
  ...extras,
});

function readStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeStorage(conversations) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
  } catch {
    console.error("Failed to persist conversation history to localStorage.");
  }
}

function titleFor(text) {
  if (!text) return "New chat";
  const clean = text.replace(/\s+/g, " ").trim().replace(/[?]/g, "");
  if (!clean) return "New chat";
  return clean.length > 45 ? `${clean.slice(0, 42).trim()}…` : clean;
}

function summary(conversation) {
  const lastMessage = conversation.messages?.at(-1);
  return {
    id: conversation.id,
    title: conversation.title || "New chat",
    preview: lastMessage?.content || "No messages yet",
    createdAt: conversation.createdAt,
    updatedAt: conversation.updatedAt || conversation.createdAt,
  };
}

function getConversationById(id) {
  return readStorage().find((item) => item.id === id);
}

function updateConversationInStorage(updated) {
  const conversations = readStorage();
  const index = conversations.findIndex((item) => item.id === updated.id);
  let next;
  if (index >= 0) {
    next = [...conversations];
    next[index] = updated;
  } else {
    next = [updated, ...conversations];
  }
  writeStorage(next);
}

export const conversationApi = {
  async list(search = "") {
    const query = search.trim().toLowerCase();
    const conversations = readStorage();
    return conversations
      .filter(
        (c) =>
          !query ||
          c.title.toLowerCase().includes(query) ||
          c.messages?.some((m) => m.content?.toLowerCase().includes(query))
      )
      .sort((a, b) => (b.updatedAt || b.createdAt).localeCompare(a.updatedAt || a.createdAt))
      .map(summary);
  },

  async create() {
    const stamp = now();
    const conversation = {
      id: crypto.randomUUID(),
      title: "New chat",
      createdAt: stamp,
      updatedAt: stamp,
      messages: [],
    };
    const conversations = readStorage();
    writeStorage([conversation, ...conversations.filter((c) => c.id !== conversation.id)]);
    return conversation;
  },

  async get(id) {
    const conversation = getConversationById(id);
    if (!conversation) {
      throw new Error("Conversation was not found in browser storage.");
    }
    return conversation;
  },

  async rename(id, title) {
    const conversation = await this.get(id);
    const updated = {
      ...conversation,
      title: title.trim().slice(0, 45) || "New chat",
      updatedAt: now(),
    };
    updateConversationInStorage(updated);
    return updated;
  },

  async remove(id) {
    const conversations = readStorage().filter((c) => c.id !== id);
    writeStorage(conversations);
  },

  async send(id, content) {
    const conversation = await this.get(id);
    const userMsg = createMessage("user", content);

    const title =
      conversation.title === "New chat" || !conversation.title
        ? titleFor(content)
        : conversation.title;

    const withUser = {
      ...conversation,
      title,
      updatedAt: userMsg.timestamp,
      messages: [...conversation.messages, userMsg],
    };
    updateConversationInStorage(withUser);

    try {
      const { data: payload } = await api.post(apiUrl("/api/chat"), {
        message: content,
        conversation_id: id,
        messages: withUser.messages.map(({ role, content: itemContent }) => ({
          role,
          content: itemContent,
        })),
      });

      if (payload.error) {
        const errorMsg = createMessage("assistant", payload.message || "The AI service returned an error.", {
          failed: true,
          errorCode: payload.code,
          errorDetails: payload.details,
        });
        const withError = {
          ...withUser,
          updatedAt: errorMsg.timestamp,
          messages: [...withUser.messages, errorMsg],
        };
        updateConversationInStorage(withError);
        return { conversation_id: id, user_message: userMsg, message: errorMsg, error: payload };
      }

      const assistantMsg = createMessage("assistant", payload.message || "Analysis complete.", {
        sql: payload.sql,
        query_result: payload.query_result,
        visualization: payload.visualization,
        diagram: payload.diagram,
        insights: payload.insights,
        tool_calls: payload.tool_calls,
      });

      const withAssistant = {
        ...withUser,
        updatedAt: assistantMsg.timestamp,
        messages: [...withUser.messages, assistantMsg],
      };
      updateConversationInStorage(withAssistant);

      return { conversation_id: id, user_message: userMsg, message: assistantMsg };
    } catch (err) {
      const safeMsg =
        err.response?.data?.message || err.message || "Failed to reach QueryNova backend API.";
      const errorMsg = createMessage("assistant", safeMsg, {
        failed: true,
        errorCode: err.response?.data?.code || "NETWORK_ERROR",
        errorDetails: err.response?.data?.details || err.message,
      });

      const withError = {
        ...withUser,
        updatedAt: errorMsg.timestamp,
        messages: [...withUser.messages, errorMsg],
      };
      updateConversationInStorage(withError);
      return { conversation_id: id, user_message: userMsg, message: errorMsg, error: err };
    }
  },

  async regenerate(conversationId, messageId) {
    const conversation = await this.get(conversationId);
    const index = conversation.messages.findIndex(
      (item) => item.id === messageId && item.role === "assistant"
    );

    if (index < 0) {
      throw new Error("Assistant message not found for regeneration.");
    }

    const priorUserMessage = [...conversation.messages.slice(0, index)]
      .reverse()
      .find((item) => item.role === "user");

    if (!priorUserMessage) {
      throw new Error("Original user message not found.");
    }

    const contextMessages = conversation.messages.slice(0, index).map(({ role, content }) => ({
      role,
      content,
    }));

    const { data: payload } = await api.post(apiUrl("/api/chat"), {
      message: priorUserMessage.content,
      conversation_id: conversationId,
      messages: contextMessages,
    });

    const updatedAssistantMsg = {
      ...createMessage("assistant", payload.message || "Analysis complete."),
      id: messageId,
      sql: payload.sql,
      query_result: payload.query_result,
      visualization: payload.visualization,
      diagram: payload.diagram,
      insights: payload.insights,
      tool_calls: payload.tool_calls,
      failed: Boolean(payload.error),
    };

    const updatedMessages = conversation.messages.map((item) =>
      item.id === messageId ? updatedAssistantMsg : item
    );

    const updatedConversation = {
      ...conversation,
      updatedAt: now(),
      messages: updatedMessages,
    };
    updateConversationInStorage(updatedConversation);

    return { conversation_id: conversationId, message: updatedAssistantMsg };
  },
};
