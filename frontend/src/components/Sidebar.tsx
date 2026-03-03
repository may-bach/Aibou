import { useState } from 'react';
import { PlusCircle, MessageSquare, ChevronLeft, ChevronRight, Bot, Trash2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import type { Chat } from '../types';

interface SidebarProps {
    chats: Chat[];
    activeChatId: string | null;
    onSelectChat: (id: string) => void;
    onNewChat: () => void;
    onDeleteChat: (id: string) => void;
}

export function Sidebar({ chats, activeChatId, onSelectChat, onNewChat, onDeleteChat }: SidebarProps) {
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [hoveredId, setHoveredId] = useState<string | null>(null);

    return (
        <motion.aside
            animate={{ width: isCollapsed ? 60 : 'var(--sidebar-width)' }}
            transition={{ duration: 0.25, ease: 'easeInOut' }}
            className="relative flex flex-col h-full bg-zinc-900 border-r border-zinc-800/60 overflow-hidden flex-shrink-0"
        >
            {/* Header */}
            <div className={`flex items-center h-14 px-3 border-b border-zinc-800/60 ${isCollapsed ? 'justify-center' : 'justify-between'}`}>
                {!isCollapsed && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="flex items-center gap-2"
                    >
                        <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                            <Bot size={13} className="text-white" />
                        </div>
                        <span className="text-sm font-semibold text-zinc-100 tracking-tight">Aibou</span>
                    </motion.div>
                )}
                <button
                    onClick={() => setIsCollapsed(!isCollapsed)}
                    className="w-7 h-7 rounded-lg flex items-center justify-center text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-all duration-150"
                >
                    {isCollapsed ? <ChevronRight size={15} /> : <ChevronLeft size={15} />}
                </button>
            </div>

            {/* New Chat button */}
            <div className={`p-2.5 ${isCollapsed ? 'flex justify-center' : ''}`}>
                <button
                    onClick={onNewChat}
                    className={`flex items-center gap-2 text-sm font-medium text-zinc-300 hover:text-white bg-zinc-800/60 hover:bg-indigo-600/80 border border-zinc-700/50 hover:border-indigo-500/40 rounded-xl transition-all duration-200 group ${isCollapsed ? 'w-9 h-9 justify-center' : 'w-full px-3 py-2.5'
                        }`}
                    title="New Chat"
                >
                    <PlusCircle size={15} className="flex-shrink-0" />
                    {!isCollapsed && <span>New Chat</span>}
                </button>
            </div>

            {/* Chat list */}
            {!isCollapsed && (
                <div className="flex-1 overflow-y-auto px-2 pb-2 space-y-0.5">
                    {chats.length === 0 && (
                        <p className="text-center text-xs text-zinc-600 mt-8 px-2">No chats yet.<br />Start a new conversation!</p>
                    )}
                    <AnimatePresence>
                        {chats.map((chat) => (
                            <motion.div
                                key={chat.id}
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -10 }}
                                transition={{ duration: 0.18 }}
                                onMouseEnter={() => setHoveredId(chat.id)}
                                onMouseLeave={() => setHoveredId(null)}
                                className={`group relative flex items-center gap-2 px-3 py-2.5 rounded-xl cursor-pointer transition-all duration-150 ${chat.id === activeChatId
                                        ? 'chat-item-active text-zinc-100'
                                        : 'text-zinc-400 hover:bg-zinc-800/60 hover:text-zinc-200'
                                    }`}
                                onClick={() => onSelectChat(chat.id)}
                            >
                                <MessageSquare size={13} className="flex-shrink-0 opacity-60" />
                                <span className="text-xs truncate flex-1">{chat.title}</span>
                                {hoveredId === chat.id && (
                                    <button
                                        onClick={(e) => { e.stopPropagation(); onDeleteChat(chat.id); }}
                                        className="flex-shrink-0 w-5 h-5 flex items-center justify-center rounded text-zinc-500 hover:text-red-400 transition-colors"
                                        title="Delete chat"
                                    >
                                        <Trash2 size={11} />
                                    </button>
                                )}
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>
            )}

            {/* Footer */}
            {!isCollapsed && (
                <div className="p-3 border-t border-zinc-800/60">
                    <div className="flex items-center gap-2 px-2 py-2 rounded-xl hover:bg-zinc-800/40 cursor-pointer transition-colors">
                        <div className="w-6 h-6 rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center flex-shrink-0">
                            <span className="text-[9px] font-bold text-white">U</span>
                        </div>
                        <span className="text-xs text-zinc-400">Local User</span>
                        <div className="ml-auto w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_4px_rgba(52,211,153,0.8)]" />
                    </div>
                </div>
            )}
        </motion.aside>
    );
}
