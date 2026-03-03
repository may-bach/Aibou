import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Message } from '../types';

interface ChatMessageProps {
    message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
    const isUser = message.role === 'user';

    if (isUser) {
        return (
            <motion.div
                className="flex justify-end px-4 py-1.5"
                initial={{ opacity: 0, y: 10, scale: 0.97 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.25, ease: 'easeOut' }}
            >
                <div className="max-w-[75%]">
                    <div className="bg-indigo-600/80 text-zinc-50 rounded-2xl rounded-br-sm px-4 py-3 text-sm leading-relaxed shadow-lg shadow-indigo-950/30 border border-indigo-500/30">
                        {message.content}
                    </div>
                    <p className="text-right text-[10px] text-zinc-600 mt-1 pr-0.5">
                        {formatTime(message.timestamp)}
                    </p>
                </div>
            </motion.div>
        );
    }

    return (
        <motion.div
            className="flex justify-start px-4 py-1.5"
            initial={{ opacity: 0, y: 10, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
        >
            {/* Avatar */}
            <div className="flex-shrink-0 mr-3 mt-0.5">
                <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-md">
                    <span className="text-[10px] font-bold text-white">AI</span>
                </div>
            </div>
            <div className="max-w-[80%]">
                <div className="bg-zinc-800/80 border border-zinc-800 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
                    <div className="prose prose-sm prose-invert max-w-none text-sm leading-relaxed text-zinc-200">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {message.content}
                        </ReactMarkdown>
                    </div>
                </div>
                <p className="text-[10px] text-zinc-600 mt-1 pl-0.5">
                    {formatTime(message.timestamp)}
                </p>
            </div>
        </motion.div>
    );
}

function formatTime(date: Date): string {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
