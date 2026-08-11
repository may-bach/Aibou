import { useRef, useCallback, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowUp, Square, Plus, FileText, X, Loader2, Mic, MicOff } from 'lucide-react';
import type { Attachment } from '../types';

const API = 'http://localhost:8000';

interface ChatInputProps {
    value: string;
    onChange: (val: string) => void;
    onSend: (content: string, attachments?: Attachment[]) => void;
    onStop: () => void;
    isThinking: boolean;
    isListening?: boolean;
    onToggleListening?: () => void;
}

export function ChatInput({
    value,
    onChange,
    onSend,
    onStop,
    isThinking,
    isListening = false,
    onToggleListening
}: ChatInputProps) {
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [attachments, setAttachments] = useState<Attachment[]>([]);
    const [isUploading, setIsUploading] = useState(false);

    // Auto-resize textarea to fit content
    const resize = () => {
        const el = textareaRef.current;
        if (!el) return;
        el.style.height = 'auto';
        el.style.height = `${el.scrollHeight}px`;
    };

    useEffect(() => {
        resize();
    }, [value, attachments]);

    const handleSend = useCallback(() => {
        const trimmed = value.trim();
        if ((!trimmed && attachments.length === 0) || isThinking || isUploading) return;
        onSend(trimmed, attachments);
        onChange('');
        setAttachments([]);
        if (textareaRef.current) textareaRef.current.style.height = 'auto';
    }, [value, attachments, isThinking, isUploading, onSend, onChange]);

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) { 
            e.preventDefault(); 
            if (isThinking) {
                onStop();
            } else {
                handleSend(); 
            }
        }
    };

    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (!files || files.length === 0) return;

        setIsUploading(true);
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const formData = new FormData();
            formData.append('file', file);

            try {
                const res = await fetch(`${API}/chat/upload`, {
                    method: 'POST',
                    body: formData,
                });
                if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
                const data = await res.json();
                if (data.success) {
                    setAttachments(prev => [
                        ...prev,
                        {
                            filename: data.filename,
                            text: data.text,
                            file_type: data.file_type,
                            size: data.size,
                        }
                    ]);
                }
            } catch (err) {
                console.error('Document upload error:', err);
            }
        }
        setIsUploading(false);
        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    const removeAttachment = (index: number) => {
        setAttachments(prev => prev.filter((_, i) => i !== index));
    };

    const canSend = (value.trim().length > 0 || attachments.length > 0) && !isThinking && !isUploading;

    return (
        <div className="input-area">
            {/* Hidden file picker input */}
            <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileSelect}
                accept=".pdf,.docx,.doc,.txt,.md,.csv,.py,.json,.js,.ts,.html,.css"
                multiple
                style={{ display: 'none' }}
            />

            <div className={`input-box ${isThinking ? 'input-box--active' : ''} ${isListening ? 'input-box--listening' : ''}`}>
                {/* Attached file preview chips */}
                <AnimatePresence>
                    {attachments.length > 0 && (
                        <motion.div
                            className="input-attachments-row"
                            initial={{ opacity: 0, y: -6 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -6 }}
                            transition={{ duration: 0.15 }}
                        >
                            {attachments.map((att, idx) => (
                                <div key={idx} className="attachment-chip">
                                    <FileText size={13} className="attachment-chip__icon" />
                                    <span className="attachment-chip__name" title={att.filename}>
                                        {att.filename.length > 25 ? att.filename.slice(0, 22) + '…' : att.filename}
                                    </span>
                                    {att.size && (
                                        <span className="attachment-chip__size">
                                            {(att.size / 1024).toFixed(0)} KB
                                        </span>
                                    )}
                                    <button
                                        type="button"
                                        className="attachment-chip__remove"
                                        onClick={() => removeAttachment(idx)}
                                        title="Remove file"
                                    >
                                        <X size={11} />
                                    </button>
                                </div>
                            ))}
                        </motion.div>
                    )}
                </AnimatePresence>

                <div className="input-box__inner">
                    {/* Plus / Attach button on the left */}
                    <button
                        type="button"
                        className="attach-btn"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isUploading}
                        title="Attach PDF, Word document, or text file"
                    >
                        {isUploading ? (
                            <Loader2 size={16} className="animate-spin" />
                        ) : (
                            <Plus size={16} strokeWidth={2.2} />
                        )}
                    </button>

                    {/* Textarea */}
                    <textarea
                        ref={textareaRef}
                        value={value}
                        onChange={(e) => onChange(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={
                            isListening
                                ? "Listening... Speak into your microphone..."
                                : attachments.length > 0
                                    ? "Add instructions for attached file(s)..."
                                    : "Message Aibou (or speak with Mic)..."
                        }
                        rows={1}
                        className="input-textarea"
                    />

                    {/* Voice Dictation Mic Button */}
                    {onToggleListening && (
                        <motion.button
                            type="button"
                            className={`mic-btn ${isListening ? 'mic-btn--active' : ''}`}
                            onClick={onToggleListening}
                            title={isListening ? "Stop listening" : "Speak to type"}
                            whileTap={{ scale: 0.9 }}
                        >
                            {isListening ? (
                                <MicOff size={16} className="mic-active-icon" />
                            ) : (
                                <Mic size={16} strokeWidth={2.2} />
                            )}
                        </motion.button>
                    )}

                    {/* Send / Stop button on the right */}
                    <AnimatePresence mode="wait">
                        {isThinking ? (
                            <motion.button
                                key="stop"
                                className="send-btn send-btn--stop"
                                onClick={onStop}
                                title="Stop generating response"
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
                                title="Send message"
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
            </div>
            <p className="input-hint"></p>
        </div>
    );
}
