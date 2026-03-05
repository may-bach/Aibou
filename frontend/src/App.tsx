import { useState, useCallback, useRef } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import { ChatInput } from './components/ChatInput';
import type { Chat, Message } from './types';

let messageCounter = 0;
let chatCounter = 0;

function createMessage(role: Message['role'], content: string): Message {
  return { id: `msg-${++messageCounter}`, role, content, timestamp: new Date() };
}

function createChat(firstMessage: string): Chat {
  return {
    id: `chat-${++chatCounter}`,
    title: truncateTitle(firstMessage),
    messages: [],
    conversationId: null,
    createdAt: new Date(),
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
  const abortRef = useRef<AbortController | null>(null);

  const activeChat = chats.find((c) => c.id === activeChatId) ?? null;
  const hasMessages = (activeChat?.messages.length ?? 0) > 0;

  // New Chat: just navigate to the home screen — no sidebar entry created yet
  const handleNewChat = useCallback(() => {
    setActiveChatId(null);
  }, []);

  const handleSend = useCallback(async (content: string) => {
    let chatId = activeChatId;
    let currentConversationId: number | null = null;

    // Only create a chat entry when a message is actually sent
    if (!chatId) {
      const chat = createChat(content);
      setChats((prev) => [chat, ...prev]);
      setActiveChatId(chat.id);
      chatId = chat.id;
    } else {
      currentConversationId = chats.find(c => c.id === chatId)?.conversationId ?? null;
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
      const res = await fetch('http://localhost:8000/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 1,
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
      prev.map((c) =>
        c.id === chatId
          ? { ...c, conversationId: newConversationId ?? c.conversationId, messages: [...c.messages, aiMsg] }
          : c
      )
    );
    setIsThinking(false);
    abortRef.current = null;
  }, [activeChatId, chats]);

  const handleStop = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const handleDeleteChat = useCallback((id: string) => {
    setChats((prev) => prev.filter((c) => c.id !== id));
    if (activeChatId === id) setActiveChatId(null);
  }, [activeChatId]);

  return (
    <div className="app-shell">
      <Sidebar
        chats={chats}
        activeChatId={activeChatId}
        hasMessages={hasMessages}
        onSelectChat={setActiveChatId}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
        onTopHover={setHeaderVisible}
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