export interface Attachment {
    filename: string;
    text: string;
    file_type?: string;
    size?: number;
}

export interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    isStreaming?: boolean;
    attachments?: Attachment[];
}

export interface Chat {
    id: string;
    title: string;
    messages: Message[];
    conversationId: number | null;
    createdAt: Date;
}
