import { useState, useCallback, useRef, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import { ChatInput } from './components/ChatInput';
import type { Chat, Message } from './types';

const API = 'http://localhost:8000';
const USER_ID = 1;

let messageCounter = 0;

function createMessage(role: Message['role'], content: string, id?: string | number, timestamp?: string): Message {
  return {
    id: id != null ? String(id) : `msg-${++messageCounter}`,
    role,
    content,
    timestamp: timestamp ? new Date(timestamp) : new Date(),
  };
}

function truncateTitle(text: string): string {
  return text.length > 40 ? text.slice(0, 40) + '…' : text;
}

// Floating header that fades in when hovering near the top-left of the main panel OR sidebar
function AppHeader({ externalVisible }: { externalVisible: boolean }) {
  const [selfVisible, setSelfVisible] = useState(false);
  const visible = selfVisible || externalVisible;
  return (
    <div
      className="app-header-zone"
      onMouseEnter={() => setSelfVisible(true)}
      onMouseLeave={() => setSelfVisible(false)}
    >
      <span className={`app-header-label ${visible ? 'app-header-label--visible' : ''}`}>
        Aibou
      </span>
    </div>
  );
}

export default function App() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [isThinking, setIsThinking] = useState(false);
  const [headerVisible, setHeaderVisible] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const abortRef = useRef<AbortController | null>(null);

  const activeChat = chats.find((c) => c.id === activeChatId) ?? null;
  const hasMessages = (activeChat?.messages.length ?? 0) > 0;

  // ── Load conversation list from backend on mount ──────────────────────────
  useEffect(() => {
    let cancelled = false;
    async function fetchConversations() {
      try {
        const res = await fetch(`${API}/chat/conversations/${USER_ID}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: Array<{ id: number; title: string; created_at: string; message_count: number }> = await res.json();
        if (cancelled) return;
        const hydrated: Chat[] = data.map((c) => ({
          id: `conv-${c.id}`,
          title: truncateTitle(c.title),
          messages: [],          // lazy – loaded when the user clicks the chat
          conversationId: c.id,
          createdAt: new Date(c.created_at),
        }));
        setChats(hydrated);
      } catch (err) {
        console.warn('Could not fetch conversation history:', err);
      } finally {
        if (!cancelled) setIsLoadingHistory(false);
      }
    }
    fetchConversations();
    return () => { cancelled = true; };
  }, []);

  // ── Lazy-load messages when switching to an unloaded conversation ─────────
  const handleSelectChat = useCallback(async (id: string) => {
    setActiveChatId(id);

    setChats((prev) => {
      const chat = prev.find((c) => c.id === id);
      // If messages are already loaded, nothing to do
      if (!chat || chat.messages.length > 0) return prev;
      return prev; // return unchanged; we'll load below
    });

    setChats((prev) => {
      const chat = prev.find((c) => c.id === id);
      if (!chat || chat.messages.length > 0 || chat.conversationId == null) return prev;
      return prev; // loading will happen in the async function below
    });

    // Check if the chat has no messages yet and has a known DB conversation ID
    const chat = chats.find((c) => c.id === id);
    if (!chat || chat.messages.length > 0 || chat.conversationId == null) return;

    try {
      const res = await fetch(`${API}/chat/conversations/${chat.conversationId}/messages`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: Array<{ id: number; role: string; content: string; created_at: string }> = await res.json();
      const messages: Message[] = data.map((m) =>
        createMessage(m.role as Message['role'], m.content, m.id, m.created_at)
      );
      setChats((prev) =>
        prev.map((c) => (c.id === id ? { ...c, messages } : c))
      );
    } catch (err) {
      console.warn('Could not load messages for conversation:', err);
    }
  }, [chats]);

  // New Chat: navigate to home screen — no sidebar entry created yet
  const handleNewChat = useCallback(() => {
    setActiveChatId(null);
  }, []);

  const handleSend = useCallback(async (content: string) => {
    let chatId = activeChatId;
    let currentConversationId: number | null = null;

    // Only create a chat entry when a message is actually sent
    if (!chatId) {
      const tempId = `local-${Date.now()}`;
      const newChat: Chat = {
        id: tempId,
        title: truncateTitle(content),
        messages: [],
        conversationId: null,
        createdAt: new Date(),
      };
      setChats((prev) => [newChat, ...prev]);
      setActiveChatId(tempId);
      chatId = tempId;
    } else {
      currentConversationId = chats.find((c) => c.id === chatId)?.conversationId ?? null;
    }

    const userMsg = createMessage('user', content);
    setChats((prev) =>
      prev.map((c) =>
        c.id === chatId
          ? { ...c, messages: [...c.messages, userMsg] }
          : c
      )
    );

    setIsThinking(true);
    abortRef.current = new AbortController();

    let aiContent = '';
    let newConversationId: number | null = null;
    try {
      const res = await fetch(`${API}/chat/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: USER_ID,
          content,
          ...(currentConversationId ? { conversation_id: currentConversationId } : {}),
        }),
        signal: abortRef.current.signal,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? `HTTP ${res.status}`);
      }

      const data = await res.json();
      aiContent = data.Aibou ?? data.Aibou_response ?? '*(No response)*';
      newConversationId = data.conversation_id ?? null;
      // Update chat title for new conversations (backend returns LLM-generated title)
      if (data.title && chatId) {
        setChats((prev) =>
          prev.map((c) =>
            c.id === chatId ? { ...c, title: data.title } : c
          )
        );
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        aiContent = '*(Stopped)*';
      } else {
        const msg = err instanceof Error ? err.message : 'Unknown error';
        aiContent = `⚠️ **Error:** ${msg}\n\nMake sure the FastAPI backend is running on port 8000.`;
      }
    }

    const aiMsg = createMessage('assistant', aiContent);
    setChats((prev) =>
      prev.map((c) => {
        if (c.id !== chatId) return c;
        const updatedConvId = newConversationId ?? c.conversationId;
        // If this is a newly created local chat and we now have the real DB id,
        // update the id prefix so future requests use the real conversation_id.
        return {
          ...c,
          conversationId: updatedConvId,
          messages: [...c.messages, aiMsg],
        };
      })
    );
    setIsThinking(false);
    abortRef.current = null;
  }, [activeChatId, chats]);

  const handleStop = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const handleDeleteChat = useCallback(async (id: string) => {
    const chat = chats.find((c) => c.id === id);
    // If this chat has a real DB conversation, delete it from the backend
    if (chat?.conversationId != null) {
      try {
        await fetch(`${API}/chat/conversations/${chat.conversationId}`, { method: 'DELETE' });
      } catch (err) {
        console.warn('Could not delete conversation from backend:', err);
        // Still remove from UI even if backend call fails
      }
    }
    setChats((prev) => prev.filter((c) => c.id !== id));
    if (activeChatId === id) setActiveChatId(null);
  }, [activeChatId, chats]);

  return (
    <div className="app-shell">
      <Sidebar
        chats={chats}
        activeChatId={activeChatId}
        hasMessages={hasMessages}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
        onTopHover={setHeaderVisible}
        isLoadingHistory={isLoadingHistory}
      />
      <div className="main-panel">
        <AppHeader externalVisible={headerVisible} />
        <ChatArea
          messages={activeChat?.messages ?? []}
          isThinking={isThinking}
          onSuggestion={handleSend}
        />
        <ChatInput
          onSend={handleSend}
          onStop={handleStop}
          isThinking={isThinking}
        />
      </div>
    </div>
  );
}