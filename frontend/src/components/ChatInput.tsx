import { useState, useRef, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowUp, Square } from 'lucide-react';

interface ChatInputProps {
    onSend: (content: string) => void;
    onStop: () => void;
    isThinking: boolean;
}

export function ChatInput({ onSend, onStop, isThinking }: ChatInputProps) {
    const [value, setValue] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Auto-resize textarea to fit content — single source of truth
    const resize = () => {
        const el = textareaRef.current;
        if (!el) return;
        el.style.height = 'auto';
        el.style.height = `${el.scrollHeight}px`;
    };

    useEffect(() => {
        resize();
    }, [value]);

    const handleSend = useCallback(() => {
        const trimmed = value.trim();
        if (!trimmed || isThinking) return;
        onSend(trimmed);
        setValue('');
        // Reset height after clearing
        if (textareaRef.current) textareaRef.current.style.height = 'auto';
    }, [value, isThinking, onSend]);

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
    };

    const canSend = value.trim().length > 0 && !isThinking;

    return (
        <div className="input-area">
            <div className={`input-box ${isThinking ? 'input-box--active' : ''}`}>
                <textarea
                    ref={textareaRef}
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Message Aibou..."
                    rows={1}
                    disabled={isThinking}
                    className="input-textarea"
                />
                <AnimatePresence mode="wait">
                    {isThinking ? (
                        <motion.button
                            key="stop"
                            className="send-btn send-btn--stop"
                            onClick={onStop}
                            title="Stop"
                            initial={{ scale: 0.7, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.7, opacity: 0 }}
                            transition={{ duration: 0.15 }}
                        >
                            <Square size={13} fill="currentColor" />
                        </motion.button>
                    ) : (
                        <motion.button
                            key="send"
                            className={`send-btn ${canSend ? 'send-btn--active' : 'send-btn--disabled'}`}
                            onClick={handleSend}
                            disabled={!canSend}
                            title="Send"
                            initial={{ scale: 0.7, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.7, opacity: 0 }}
                            transition={{ duration: 0.15 }}
                            whileTap={canSend ? { scale: 0.9 } : {}}
                        >
                            <ArrowUp size={16} strokeWidth={2.5} />
                        </motion.button>
                    )}
                </AnimatePresence>
            </div>
            <p className="input-hint">Shift+Enter for new line · Aibou runs locally</p>
        </div>
    );
}
