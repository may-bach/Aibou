import { useState } from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check } from 'lucide-react';
import type { Message } from '../types';

function CopyButton({ text }: { text: string }) {
    const [copied, setCopied] = useState(false);
    const handle = async () => {
        await navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };
    return (
        <button className="copy-btn" onClick={handle} title="Copy">
            {copied ? <Check size={13} /> : <Copy size={13} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
        </button>
    );
}

const msgVariants = {
    hidden: { opacity: 0, y: 14, scale: 0.98 },
    visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.22, ease: [0.25, 0.1, 0.25, 1] } },
};

export function ChatMessage({ message }: { message: Message }) {
    const isUser = message.role === 'user';

    return (
        <motion.div
            className={`msg-row ${isUser ? 'msg-row--user' : 'msg-row--ai'}`}
            variants={msgVariants}
            initial="hidden"
            animate="visible"
        >
            <div className={`msg-bubble ${isUser ? 'msg-bubble--user' : 'msg-bubble--ai'}`}>
                {isUser ? (
                    <p className="msg-text">{message.content}</p>
                ) : (
                    <>
                        <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                                code({ className, children, ...props }) {
                                    const match = /language-(\w+)/.exec(className || '');
                                    const codeText = String(children).replace(/\n$/, '');
                                    if (match) {
                                        return (
                                            <div className="code-block">
                                                <div className="code-block__header">
                                                    <span className="code-block__lang">{match[1]}</span>
                                                    <CopyButton text={codeText} />
                                                </div>
                                                <SyntaxHighlighter
                                                    style={oneDark}
                                                    language={match[1]}
                                                    PreTag="div"
                                                    customStyle={{ margin: 0, borderRadius: '0 0 8px 8px', fontSize: '13px', background: '#0d0d0d' }}
                                                    {...(props as object)}
                                                >
                                                    {codeText}
                                                </SyntaxHighlighter>
                                            </div>
                                        );
                                    }
                                    return <code className="inline-code" {...props}>{children}</code>;
                                },
                                p: ({ children }) => <p className="md-p">{children}</p>,
                                ul: ({ children }) => <ul className="md-ul">{children}</ul>,
                                ol: ({ children }) => <ol className="md-ol">{children}</ol>,
                                li: ({ children }) => <li className="md-li">{children}</li>,
                                h1: ({ children }) => <h1 className="md-h1">{children}</h1>,
                                h2: ({ children }) => <h2 className="md-h2">{children}</h2>,
                                h3: ({ children }) => <h3 className="md-h3">{children}</h3>,
                                blockquote: ({ children }) => <blockquote className="md-blockquote">{children}</blockquote>,
                                strong: ({ children }) => <strong className="md-strong">{children}</strong>,
                                hr: () => <hr className="md-hr" />,
                            }}
                        >
                            {message.content}
                        </ReactMarkdown>
                        <div className="msg-meta">
                            <span className="msg-time">{formatTime(message.timestamp)}</span>
                            <CopyButton text={message.content} />
                        </div>
                    </>
                )}
            </div>
        </motion.div>
    );
}

function formatTime(date: Date): string {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
