import { useEffect, useRef } from 'react';
import { ChatMessage } from './ChatMessage';
import { ThinkingIndicator } from './ThinkingIndicator';
import { Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';
import type { Message } from '../types';

interface ChatAreaProps {
    messages: Message[];
    isThinking: boolean;
}

export function ChatArea({ messages, isThinking }: ChatAreaProps) {
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isThinking]);

    if (messages.length === 0) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center gap-4 px-4 select-none">
                <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.5, ease: 'easeOut' }}
                    className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-600 to-pink-600 flex items-center justify-center shadow-2xl shadow-indigo-900/40"
                >
                    <Sparkles size={28} className="text-white" />
                </motion.div>
                <motion.div
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.1 }}
                    className="text-center"
                >
                    <h2 className="text-2xl font-semibold text-zinc-100 mb-1">Hi, I'm Aibou</h2>
                    <p className="text-sm text-zinc-500 max-w-xs">
                        Your local AI assistant. Ask me anything — code, questions, ideas.
                    </p>
                </motion.div>
                <motion.div
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: 0.25 }}
                    className="grid grid-cols-2 gap-2 mt-2 w-full max-w-sm"
                >
                    {SUGGESTIONS.map((s) => (
                        <div
                            key={s}
                            className="text-xs text-zinc-400 bg-zinc-900 border border-zinc-800 rounded-xl px-3 py-2.5 cursor-pointer hover:border-indigo-500/40 hover:text-zinc-200 hover:bg-zinc-800/60 transition-all duration-150"
                        >
                            {s}
                        </div>
                    ))}
                </motion.div>
            </div>
        );
    }

    return (
        <div className="flex-1 overflow-y-auto py-2">
            {messages.map((msg) => (
                <ChatMessage key={msg.id} message={msg} />
            ))}
            {isThinking && <ThinkingIndicator />}
            <div ref={bottomRef} className="h-2" />
        </div>
    );
}

const SUGGESTIONS = [
    '✨ Write a poem about the stars',
    '🐍 Explain Python generators',
    '🎨 Design a UI component',
    '🔍 How does RAG work?',
];
