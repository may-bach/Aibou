import { useState, useCallback } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import { ChatInput } from './components/ChatInput';
import type { Chat, Message } from './types';

let messageCounter = 0;
let chatCounter = 0;

function createMessage(role: Message['role'], content: string): Message {
  return {
    id: `msg-${++messageCounter}`,
    role,
    content,
    timestamp: new Date(),
  };
}

function createChat(firstMessage?: string): Chat {
  return {
    id: `chat-${++chatCounter}`,
    title: firstMessage ? truncateTitle(firstMessage) : 'New Chat',
    messages: [],
    createdAt: new Date(),
  };
}

function truncateTitle(text: string): string {
  return text.length > 32 ? text.slice(0, 32) + '…' : text;
}

export default function App() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [isThinking, setIsThinking] = useState(false);

  const activeChat = chats.find((c) => c.id === activeChatId) ?? null;

  const handleNewChat = useCallback(() => {
    const chat = createChat();
    setChats((prev) => [chat, ...prev]);
    setActiveChatId(chat.id);
  }, []);

  const handleSend = useCallback(async (content: string) => {
    let chatId = activeChatId;

    if (!chatId) {
      const chat = createChat(content);
      setChats((prev) => [chat, ...prev]);
      setActiveChatId(chat.id);
      chatId = chat.id;
    }

    const userMsg = createMessage('user', content);

    setChats((prev) =>
      prev.map((c) =>
        c.id === chatId
          ? {
            ...c,
            title: c.messages.length === 0 ? truncateTitle(content) : c.title,
            messages: [...c.messages, userMsg],
          }
          : c
      )
    );

    setIsThinking(true);

    let aiContent = "";
    try {
      // Send the real request to your FastAPI backend
      const response = await fetch("http://localhost:8000/chat/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: 1, // Your user ID from the database
          content: content
        }),
      });

      if (!response.ok) throw new Error("Network error");

      const data = await response.json();
      aiContent = data.Aibou_response; // Get the real response from the swarm

    } catch (error) {
      console.error("Error talking to Aibou:", error);
      aiContent = "⚠️ **Connection Error:** Could not reach the local Aibou backend. Is the FastAPI server running on port 8000?";
    }

    const aiMsg = createMessage('assistant', aiContent);

    setChats((prev) =>
      prev.map((c) =>
        c.id === chatId
          ? { ...c, messages: [...c.messages, aiMsg] }
          : c
      )
    );
    setIsThinking(false);
  }, [activeChatId]);

  const handleDeleteChat = useCallback((id: string) => {
    setChats((prev) => prev.filter((c) => c.id !== id));
    if (activeChatId === id) {
      setActiveChatId(null);
    }
  }, [activeChatId]);

  return (
    <div className="flex h-screen w-screen bg-zinc-950 text-zinc-100 overflow-hidden">
      <Sidebar
        chats={chats}
        activeChatId={activeChatId}
        onSelectChat={setActiveChatId}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
      />

      {/* Main area */}
      <div className="flex flex-col flex-1 min-w-0 h-full">
        {/* Topbar */}
        <header className="flex items-center h-14 px-5 border-b border-zinc-800/60 flex-shrink-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-zinc-200">
              {activeChat ? activeChat.title : 'Aibou'}
            </span>
            {isThinking && (
              <span className="text-[10px] text-indigo-400 font-medium animate-pulse">● thinking</span>
            )}
          </div>
          <div className="ml-auto flex items-center gap-2">
            <span className="text-[10px] text-zinc-600 px-2 py-1 bg-zinc-900 border border-zinc-800 rounded-lg">
              local model
            </span>
          </div>
        </header>

        {/* Chat + Input */}
        <ChatArea
          messages={activeChat?.messages ?? []}
          isThinking={isThinking}
        />
        <ChatInput onSend={handleSend} isThinking={isThinking} />
      </div>
    </div>
  );
}