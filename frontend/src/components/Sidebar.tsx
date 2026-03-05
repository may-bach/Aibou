import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, MessageSquare, Trash2 } from 'lucide-react';
import type { Chat } from '../types';

interface SidebarProps {
    chats: Chat[];
    activeChatId: string | null;
    hasMessages: boolean;
    onSelectChat: (id: string) => void;
    onNewChat: () => void;
    onDeleteChat: (id: string) => void;
    onTopHover: (v: boolean) => void; // notifies App when sidebar top is hovered
}

export function Sidebar({ chats, activeChatId, hasMessages, onSelectChat, onNewChat, onDeleteChat, onTopHover }: SidebarProps) {
    const [hoveredId, setHoveredId] = useState<string | null>(null);
    const [pinned, setPinned] = useState(true);
    const [hovered, setHovered] = useState(false);
    const prevHasMessages = useRef(false);

    useEffect(() => {
        if (hasMessages && !prevHasMessages.current) {
            setPinned(false);
        }
        prevHasMessages.current = hasMessages;
    }, [hasMessages]);

    const isOpen = pinned || hovered;

    const handleMouseEnter = () => {
        setHovered(true);
        onTopHover(true);
    };
    const handleMouseLeave = () => {
        setHovered(false);
        onTopHover(false);
    };

    return (
        <motion.aside
            className="sidebar"
            animate={{ width: isOpen ? 'var(--sidebar-w)' : 48 }}
            transition={{ duration: 0.22, ease: [0.4, 0, 0.2, 1] }}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
        >
            <div className="sidebar__header">
                {/* Logo — always visible; animates margin left/right with sidebar */}
                <motion.div
                    className="sidebar__logo-icon"
                    animate={{ marginLeft: isOpen ? 17 : 15 }}
                    transition={{ duration: 0.22, ease: [0.4, 0, 0.2, 1] }}
                >
                    <img src="/Aibou_2-removebg-preview.png" alt="Aibou Logo" className="sidebar__logo-image" />
                </motion.div>

                {/* Pin button — only visible when expanded */}
                <AnimatePresence>
                    {isOpen && (
                        <motion.button
                            className="icon-btn"
                            onClick={() => setPinned(p => !p)}
                            title={pinned ? 'Collapse sidebar' : 'Pin sidebar open'}
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.15 }}
                            whileTap={{ scale: 0.9 }}
                        >
                            <Plus
                                size={15}
                                style={{ transform: pinned ? 'rotate(45deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}
                            />
                        </motion.button>
                    )}
                </AnimatePresence>
            </div>

            <div className="sidebar__new">
                <motion.button
                    className={`new-chat-btn ${isOpen ? 'new-chat-btn--full' : 'new-chat-btn--icon'}`}
                    onClick={onNewChat}
                    title="New Chat"
                    whileTap={{ scale: 0.96 }}
                >
                    <Plus size={15} />
                    <AnimatePresence>
                        {isOpen && (
                            <motion.span
                                initial={{ opacity: 0, width: 0 }}
                                animate={{ opacity: 1, width: 'auto' }}
                                exit={{ opacity: 0, width: 0 }}
                                transition={{ duration: 0.15 }}
                                style={{ overflow: 'hidden', whiteSpace: 'nowrap' }}
                            >
                                New Chat
                            </motion.span>
                        )}
                    </AnimatePresence>
                </motion.button>
            </div>

            <AnimatePresence>
                {isOpen && (
                    <motion.nav
                        className="sidebar__list"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.15 }}
                    >
                        <AnimatePresence initial={false}>
                            {chats.length === 0 ? (
                                <motion.p key="empty" className="sidebar__empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                                    No conversations yet.<br />Start typing to begin!
                                </motion.p>
                            ) : (
                                chats.map((chat) => (
                                    <motion.div
                                        key={chat.id}
                                        className={`chat-item ${chat.id === activeChatId ? 'chat-item--active' : ''}`}
                                        initial={{ opacity: 0, x: -8 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0, x: -8, height: 0 }}
                                        transition={{ duration: 0.16 }}
                                        onClick={() => onSelectChat(chat.id)}
                                        onMouseEnter={() => setHoveredId(chat.id)}
                                        onMouseLeave={() => setHoveredId(null)}
                                    >
                                        <MessageSquare size={12} className="chat-item__icon" />
                                        <span className="chat-item__title">{chat.title}</span>
                                        <AnimatePresence>
                                            {hoveredId === chat.id && (
                                                <motion.button
                                                    key="del"
                                                    className="chat-item__delete"
                                                    onClick={(e) => { e.stopPropagation(); onDeleteChat(chat.id); }}
                                                    initial={{ opacity: 0, scale: 0.8 }}
                                                    animate={{ opacity: 1, scale: 1 }}
                                                    exit={{ opacity: 0, scale: 0.8 }}
                                                    transition={{ duration: 0.1 }}
                                                >
                                                    <Trash2 size={12} />
                                                </motion.button>
                                            )}
                                        </AnimatePresence>
                                    </motion.div>
                                ))
                            )}
                        </AnimatePresence>
                    </motion.nav>
                )}
            </AnimatePresence>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        className="sidebar__footer"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.12 }}
                    >
                        <div className="user-pill">
                            <div className="user-pill__avatar">U</div>
                            <span className="user-pill__name">Local User</span>
                            <div className="user-pill__dot" />
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.aside>
    );
}
