import { useRef, useState, useCallback } from 'react';
import { ArrowUp } from 'lucide-react';
import { motion } from 'framer-motion';

interface ChatInputProps {
    onSend: (content: string) => void;
    isThinking: boolean;
}

export function ChatInput({ onSend, isThinking }: ChatInputProps) {
    const [value, setValue] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const handleSend = useCallback(() => {
        const trimmed = value.trim();
        if (!trimmed || isThinking) return;
        onSend(trimmed);
        setValue('');
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
        }
    }, [value, isThinking, onSend]);

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const canSend = value.trim().length > 0 && !isThinking;

    return (
        <div className="px-4 pb-4 pt-2">
            <div className="relative flex items-end gap-2 bg-zinc-900 border border-zinc-700/60 rounded-2xl px-4 py-3 shadow-[inset_0_1px_4px_rgba(0,0,0,0.4)] focus-within:border-indigo-500/50 focus-within:shadow-[inset_0_1px_4px_rgba(0,0,0,0.4),0_0_0_1px_rgba(99,102,241,0.15)] transition-all duration-200">
                <textarea
                    ref={textareaRef}
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Message Aibou..."
                    rows={1}
                    disabled={isThinking}
                    className="flex-1 resize-none bg-transparent text-sm text-zinc-100 placeholder-zinc-500 outline-none leading-relaxed max-h-48 overflow-y-auto disabled:opacity-50"
                    style={{ minHeight: '24px' }}
                />
                <motion.button
                    onClick={handleSend}
                    disabled={!canSend}
                    whileHover={canSend ? { scale: 1.05 } : {}}
                    whileTap={canSend ? { scale: 0.95 } : {}}
                    className={`flex-shrink-0 ml-1 mb-0.5 w-8 h-8 rounded-xl flex items-center justify-center transition-all duration-200 send-btn-glow ${canSend
                            ? 'bg-indigo-600 text-white cursor-pointer shadow-md shadow-indigo-900/40'
                            : 'bg-zinc-700/50 text-zinc-500 cursor-not-allowed'
                        }`}
                >
                    <ArrowUp size={16} strokeWidth={2.5} />
                </motion.button>
            </div>
            <p className="text-center text-[10px] text-zinc-600 mt-2">
                Aibou can make mistakes. Shift+Enter for new line.
            </p>
        </div>
    );
}
