import { useState, useCallback, useRef, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import { ChatInput } from './components/ChatInput';
import { SettingsModal } from './components/SettingsModal';
import { useVoice } from './hooks/useVoice';
import { Volume2, VolumeX, ChevronDown } from 'lucide-react';
import type { Chat, Message, Attachment } from './types';



const API = 'http://localhost:8000';
const USER_ID = 1;

let messageCounter = 0;

function createMessage(
  role: Message['role'],
  content: string,
  id?: string | number,
  timestamp?: string,
  isStreaming?: boolean
): Message {
  return {
    id: id != null ? String(id) : `msg-${++messageCounter}`,
    role,
    content,
    timestamp: timestamp ? new Date(timestamp) : new Date(),
    isStreaming: Boolean(isStreaming),
  };
}

function truncateTitle(text: string): string {
  return text.length > 40 ? text.slice(0, 40) + '…' : text;
}

function AppHeader({
  externalVisible,
  autoVoiceEnabled,
  onToggleAutoVoice,
  selectedVoice,
  onSelectVoice,
  availableVoices,
  isSpeaking,
  onStopSpeaking
}: {
  externalVisible: boolean;
  autoVoiceEnabled: boolean;
  onToggleAutoVoice: () => void;
  selectedVoice: string;
  onSelectVoice: (id: string) => void;
  availableVoices: Array<{ id: string; name: string; style: string }>;
  isSpeaking: boolean;
  onStopSpeaking: () => void;
}) {
  const [selfVisible, setSelfVisible] = useState(false);
  const [showVoiceMenu, setShowVoiceMenu] = useState(false);
  const visible = selfVisible || externalVisible || autoVoiceEnabled || isSpeaking;

  const currentVoiceObj = availableVoices.find(v => v.id === selectedVoice);

  return (
    <div
      className="app-header-zone"
      onMouseEnter={() => setSelfVisible(true)}
      onMouseLeave={() => { setSelfVisible(false); setShowVoiceMenu(false); }}
    >
      <div className={`app-header-bar ${visible ? 'app-header-bar--visible' : ''}`}>
        <span className="app-header-label">Aibou</span>

        <div className="header-voice-controls">
          <button
            className={`voice-toggle-btn ${autoVoiceEnabled ? 'voice-toggle-btn--active' : ''}`}
            onClick={onToggleAutoVoice}
            title={autoVoiceEnabled ? "Auto-Voice Mode ON (Speaks replies out loud)" : "Auto-Voice Mode OFF"}
          >
            {autoVoiceEnabled ? (
              <>
                <Volume2 size={13} className="voice-icon-active" />
                <span>Auto Voice</span>
              </>
            ) : (
              <>
                <VolumeX size={13} />
                <span>Muted</span>
              </>
            )}
          </button>

          <div className="voice-selector-wrap">
            <button
              className="voice-picker-btn"
              onClick={() => setShowVoiceMenu(prev => !prev)}
              title="Select Voice Profile"
            >
              <span>{currentVoiceObj ? currentVoiceObj.name : 'Voice'}</span>
              <ChevronDown size={11} />
            </button>

            {showVoiceMenu && (
              <div className="voice-dropdown-menu">
                <div className="voice-dropdown-header">Voice Personality</div>
                {availableVoices.map(v => (
                  <button
                    key={v.id}
                    className={`voice-option ${v.id === selectedVoice ? 'voice-option--selected' : ''}`}
                    onClick={() => {
                      onSelectVoice(v.id);
                      setShowVoiceMenu(false);
                    }}
                  >
                    <span className="voice-name">{v.name}</span>
                    <span className="voice-style">{v.style}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {isSpeaking && (
            <button
              className="stop-speaking-chip"
              onClick={onStopSpeaking}
              title="Stop audio playback"
            >
              <span className="stop-dot" />
              <span>Speaking</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [activeNodes, setActiveNodes] = useState<Record<string, string>>({});
  const activeNode = activeChatId ? activeNodes[activeChatId] || null : null;
  const [inputValue, setInputValue] = useState('');
  const [headerVisible, setHeaderVisible] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [useLocalLLM, setUseLocalLLM] = useState(true);
  const [activeModelName, setActiveModelName] = useState('qwen2.5:14b');
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | undefined>(undefined);

  const fetchProviderSettings = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/v1/config/settings`);
      if (res.ok) {
        const data = await res.json();
        setUseLocalLLM(Boolean(data.use_local_llm));
        setActiveModelName(data.active_chat_model || 'qwen2.5:14b');
      }
    } catch (err) {
      console.warn('Could not fetch provider settings:', err);
    }
  }, []);

  useEffect(() => {
    fetchProviderSettings();
  }, [fetchProviderSettings]);


  const {
    isListening,
    isSpeaking,
    currentSpeakingId,
    selectedVoice,
    setSelectedVoice,
    autoVoiceEnabled,
    setAutoVoiceEnabled,
    availableVoices,
    speak,
    stopSpeaking,
    toggleListening
  } = useVoice();

  const activeChat = chats.find((c) => c.id === activeChatId) ?? null;
  const hasMessages = (activeChat?.messages.length ?? 0) > 0;

  // Fetch conversations from db on mount
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
          messages: [],
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

  // WebSocket connection & live streaming
  useEffect(() => {

    let reconnectDelay = 1000;
    let shouldReconnect = true;

    function connect() {
      const wsUrl = `ws://localhost:8000/chat/ws/${USER_ID}`;
      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        reconnectDelay = 1000;
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          const chatIdKey = payload.local_chat_id || (payload.conversation_id ? `conv-${payload.conversation_id}` : null);

          // 1. Swarm status / Active node changes
          if (payload.type === 'status') {
            if (chatIdKey) {
              setActiveNodes(prev => ({ ...prev, [chatIdKey]: payload.node }));
            }
            return;
          }

          // 2. Tool execution status
          if (payload.type === 'tool_status') {
            if (chatIdKey) {
              if (payload.status === 'running') {
                setActiveNodes(prev => ({ ...prev, [chatIdKey]: payload.tool }));
              } else {
                setActiveNodes(prev => ({ ...prev, [chatIdKey]: 'Specialist' }));
              }
            }
            return;
          }

          // 3. Real-time token streaming
          if (payload.type === 'token') {
            if (chatIdKey) {
              setActiveNodes(prev => {
                const next = { ...prev };
                delete next[chatIdKey];
                return next;
              });

              setChats(prev =>
                prev.map(c => {
                  const isMatch = (payload.conversation_id && c.conversationId === payload.conversation_id) ||
                                  (payload.local_chat_id && c.id === payload.local_chat_id);
                  if (!isMatch) return c;

                  const msgs = [...c.messages];
                  const lastMsg = msgs[msgs.length - 1];

                  if (lastMsg && lastMsg.role === 'assistant' && lastMsg.isStreaming) {
                    msgs[msgs.length - 1] = {
                      ...lastMsg,
                      content: lastMsg.content + payload.delta,
                    };
                  } else {
                    msgs.push({
                      id: `stream-${Date.now()}`,
                      role: 'assistant',
                      content: payload.delta,
                      timestamp: new Date(),
                      isStreaming: true,
                    });
                  }

                  return {
                    ...c,
                    messages: msgs,
                  };
                })
              );
            }
            return;
          }

          // 4. Response complete
          if (payload.type === 'complete') {
            if (chatIdKey) {
              setActiveNodes(prev => {
                const next = { ...prev };
                delete next[chatIdKey];
                return next;
              });
            }

            const replyText = payload.message || '';
            const msgId = `msg-${Date.now()}`;

            setChats(prev =>
              prev.map(c => {
                const isMatch = (payload.conversation_id && c.conversationId === payload.conversation_id) ||
                                (payload.local_chat_id && c.id === payload.local_chat_id);
                if (!isMatch) return c;

                const msgs = [...c.messages];
                const lastMsg = msgs[msgs.length - 1];

                if (lastMsg && lastMsg.role === 'assistant') {
                  msgs[msgs.length - 1] = {
                    ...lastMsg,
                    id: lastMsg.id || msgId,
                    content: replyText || lastMsg.content,
                    isStreaming: false,
                  };
                } else {
                  msgs.push(createMessage('assistant', replyText, msgId));
                }

                return {
                  ...c,
                  conversationId: payload.conversation_id || c.conversationId,
                  title: payload.title ? truncateTitle(payload.title) : c.title,
                  messages: msgs,
                };
              })
            );

            // If auto-voice is enabled, speak the completed reply out loud
            if (autoVoiceEnabled && replyText) {
              speak(replyText, msgId);
            }

            return;
          }

          // 5. Pipeline Error
          if (payload.type === 'error') {
            console.error('Aibou WS Error:', payload.message);
            const errMsg = createMessage('assistant', `⚠️ **Error:** ${payload.message}`);
            if (chatIdKey) {
              setChats(prev =>
                prev.map(c =>
                  c.id === chatIdKey || (c.conversationId && `conv-${c.conversationId}` === chatIdKey)
                    ? { ...c, messages: [...c.messages, errMsg] }
                    : c
                )
              );
              setActiveNodes(prev => {
                const next = { ...prev };
                delete next[chatIdKey];
                return next;
              });
            }
            return;
          }

        } catch (err) {
          console.error('Failed to parse WS message:', err);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        if (shouldReconnect) {
          reconnectTimeoutRef.current = window.setTimeout(() => {
            reconnectDelay = Math.min(reconnectDelay * 2, 10000);
            connect();
          }, reconnectDelay);
        }
      };

      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
      };
    }

    connect();

    return () => {
      shouldReconnect = false;
      window.clearTimeout(reconnectTimeoutRef.current);
      socketRef.current?.close();
    };
  }, [autoVoiceEnabled, speak]);

  // Lazy load chat messages
  const handleSelectChat = useCallback(async (id: string) => {
    setActiveChatId(id);
    stopSpeaking();

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
  }, [chats, stopSpeaking]);

  const handleNewChat = useCallback(() => {
    setActiveChatId(null);
    stopSpeaking();
  }, [stopSpeaking]);


  const handleSend = useCallback((content: string, attachments?: Attachment[]) => {
    stopSpeaking();
    let chatId = activeChatId;
    let currentConversationId: number | null = null;

    const displayTitle = content || (attachments && attachments.length > 0 ? `Doc: ${attachments[0].filename}` : "New Chat");

    if (!chatId) {
      const tempId = `local-${Date.now()}`;
      const newChat: Chat = {
        id: tempId,
        title: truncateTitle(displayTitle),
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

    const displayContent = content || (attachments && attachments.length > 0 ? `📎 Attached: ${attachments.map(a => a.filename).join(', ')}` : "");
    const userMsg = createMessage('user', displayContent);
    if (attachments && attachments.length > 0) {
      userMsg.attachments = attachments;
    }

    setChats((prev) =>
      prev.map((c) =>
        c.id === chatId
          ? { ...c, messages: [...c.messages, userMsg] }
          : c
      )
    );

    setActiveNodes(prev => ({ ...prev, [chatId!]: "Aibou" }));

    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({
        content,
        attachments: attachments || [],
        conversation_id: currentConversationId,
        local_chat_id: chatId
      }));
    } else {
      console.warn('WebSocket is not connected. Message not sent.');
      setActiveNodes(prev => {
        const next = { ...prev };
        delete next[chatId!];
        return next;
      });
    }
  }, [activeChatId, chats, stopSpeaking]);

  const handleStop = useCallback(() => {
    stopSpeaking();
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.close();
    }
    if (activeChatId) {
      setActiveNodes(prev => {
        const next = { ...prev };
        delete next[activeChatId];
        return next;
      });
    }
  }, [activeChatId, stopSpeaking]);

  const handleEditMessage = useCallback((content: string) => {
    setInputValue(content);
  }, []);

  const handleDeleteChat = useCallback(async (id: string) => {
    stopSpeaking();
    const chat = chats.find((c) => c.id === id);
    if (chat?.conversationId != null) {
      try {
        await fetch(`${API}/chat/conversations/${chat.conversationId}`, { method: 'DELETE' });
      } catch (err) {
        console.warn('Could not delete conversation from backend:', err);
      }
    }
    setChats((prev) => prev.filter((c) => c.id !== id));
    if (activeChatId === id) setActiveChatId(null);
  }, [activeChatId, chats, stopSpeaking]);

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
        onOpenSettings={() => setIsSettingsOpen(true)}
        useLocalLLM={useLocalLLM}
        activeModelName={activeModelName}
        isLoadingHistory={isLoadingHistory}
      />
      <div className="main-panel">
        <AppHeader
          externalVisible={headerVisible}
          autoVoiceEnabled={autoVoiceEnabled}
          onToggleAutoVoice={() => setAutoVoiceEnabled(prev => !prev)}
          selectedVoice={selectedVoice}
          onSelectVoice={setSelectedVoice}
          availableVoices={availableVoices}
          isSpeaking={isSpeaking}
          onStopSpeaking={stopSpeaking}
        />
        <ChatArea
          messages={activeChat?.messages ?? []}
          activeNode={activeNode}
          onSuggestion={handleSend}
          onEdit={handleEditMessage}
          onSpeak={speak}
          currentSpeakingId={currentSpeakingId}
        />
        <ChatInput
          value={inputValue}
          onChange={setInputValue}
          onSend={handleSend}
          onStop={handleStop}
          isThinking={activeNode !== null}
          isListening={isListening}
          onToggleListening={() => toggleListening(() => inputValue, setInputValue)}
        />
      </div>
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onSettingsChanged={fetchProviderSettings}
      />
    </div>
  );
}