import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChatMessage } from './ChatMessage';
import { ThinkingIndicator } from './ThinkingIndicator';
import { Sparkles } from 'lucide-react';
import type { Message } from '../types';

interface ChatAreaProps {
    messages: Message[];
    activeNode: string | null;
    onSuggestion: (text: string) => void;
    onEdit: (text: string) => void;
}

const SUGGESTIONS = [
    'Explain Python generators with examples',
    'Write a REST API with FastAPI',
    'How does RAG work in AI systems?',
    'Debug this: list index out of range',
];

export function ChatArea({ messages, activeNode, onSuggestion, onEdit }: ChatAreaProps) {
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, activeNode]);

    return (
        <AnimatePresence mode="wait">
            {messages.length === 0 ? (
                <motion.div
                    key="welcome"
                    className="welcome"
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -12 }}
                    transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
                >
                    <motion.div
                        className="welcome__icon-wrap"
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ delay: 0.05, duration: 0.35, type: 'spring', stiffness: 260, damping: 20 }}
                    >
                        <Sparkles size={24} className="welcome__icon" />
                    </motion.div>
                    <motion.h1
                        className="welcome__heading"
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.12, duration: 0.3 }}
                    >
                        How can I help you today?
                    </motion.h1>
                    <motion.p
                        className="welcome__sub"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.2, duration: 0.3 }}
                    >
                        Your local AI assistant — code, questions, creative writing.
                    </motion.p>
                    <motion.div
                        className="suggestions"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.28, duration: 0.3 }}
                    >
                        {SUGGESTIONS.map((s, i) => (
                            <motion.button
                                key={s}
                                className="suggestion-chip"
                                onClick={() => onSuggestion(s)}
                                initial={{ opacity: 0, y: 8 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.32 + i * 0.05, duration: 0.25 }}
                                whileHover={{ scale: 1.015, borderColor: '#3a3a3a' }}
                                whileTap={{ scale: 0.98 }}
                            >
                                {s}
                            </motion.button>
                        ))}
                    </motion.div>
                </motion.div>
            ) : (
                <motion.div
                    key="feed"
                    className="chat-scroll"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.2 }}
                >
                    <div className="chat-feed">
                        {messages.map((msg) => (
                            <ChatMessage key={msg.id} message={msg} onEdit={onEdit} />
                        ))}
                        {activeNode && <ThinkingIndicator activeNode={activeNode} />}
                        <div ref={bottomRef} />
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
