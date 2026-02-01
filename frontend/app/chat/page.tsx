'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type { ChatRequest } from '@/lib/types';
import Link from 'next/link';
import { ArrowLeft, Loader2, MessageSquare, Send } from 'lucide-react';

type Message = {
    role: 'user' | 'assistant';
    content: string;
};

export default function ChatPage() {
    const [message, setMessage] = useState('');
    const [history, setHistory] = useState<Message[]>([]);
    const [useLibraryRAG, setUseLibraryRAG] = useState(false);

    const chatMutation = useMutation({
        mutationFn: (request: ChatRequest) => apiClient.chat(request),
        onSuccess: (data) => {
            if (data.success && data.response) {
                setHistory((prev) => [...prev, { role: 'assistant', content: data.response! }]);
            }
        },
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!message.trim()) return;

        // Add user message to history
        const userMessage: Message = { role: 'user', content: message };
        setHistory((prev) => [...prev, userMessage]);

        // Send to API
        chatMutation.mutate({
            message,
            history: history.map((m) => ({ role: m.role, content: m.content })),
            use_library_rag: useLibraryRAG,
        });

        setMessage('');
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-950">
            {/* Header */}
            <header className="border-b border-white/10 bg-black/20 backdrop-blur-sm">
                <div className="container mx-auto px-6 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <Link href="/" className="rounded-lg p-2 hover:bg-white/10 transition-colors">
                                <ArrowLeft className="h-5 w-5 text-blue-400" />
                            </Link>
                            <div className="flex items-center gap-3">
                                <MessageSquare className="h-6 w-6 text-blue-400" />
                                <h1 className="text-xl font-bold text-white">AI Chat</h1>
                            </div>
                        </div>
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={useLibraryRAG}
                                onChange={(e) => setUseLibraryRAG(e.target.checked)}
                                className="rounded border-blue-500/30 bg-slate-900/50 text-blue-600 focus:ring-2 focus:ring-blue-500/50"
                            />
                            <span className="text-sm text-blue-200">Use Library</span>
                        </label>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="container mx-auto px-6 py-6 flex flex-col" style={{ height: 'calc(100vh - 80px)' }}>
                <div className="mx-auto w-full max-w-4xl flex flex-col flex-1">
                    {/* Chat Messages */}
                    <div className="flex-1 overflow-y-auto rounded-2xl border border-blue-500/20 bg-gradient-to-br from-blue-900/40 to-slate-900/40 p-6 backdrop-blur-sm mb-6">
                        {history.length === 0 ? (
                            <div className="flex h-full items-center justify-center text-blue-300/60">
                                Start a conversation...
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {history.map((msg, idx) => (
                                    <div
                                        key={idx}
                                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                                    >
                                        <div
                                            className={`max-w-[80%] rounded-2xl px-4 py-3 ${msg.role === 'user'
                                                ? 'bg-blue-600 text-white'
                                                : 'bg-slate-800/80 text-blue-100'
                                                }`}
                                        >
                                            <p className="whitespace-pre-wrap">{msg.content}</p>
                                        </div>
                                    </div>
                                ))}
                                {chatMutation.isPending && (
                                    <div className="flex justify-start">
                                        <div className="max-w-[80%] rounded-2xl bg-slate-800/80 px-4 py-3">
                                            <Loader2 className="h-5 w-5 animate-spin text-blue-400" />
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Input Form */}
                    <form onSubmit={handleSubmit} className="flex gap-2">
                        <input
                            type="text"
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                            placeholder="Ask me anything..."
                            className="flex-1 rounded-lg border border-blue-500/30 bg-slate-900/50 px-4 py-3 text-white placeholder-blue-300/40 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                        />
                        <button
                            type="submit"
                            disabled={chatMutation.isPending || !message.trim()}
                            className="rounded-lg bg-blue-600 px-6 py-3 font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                        >
                            <Send className="h-5 w-5" />
                        </button>
                    </form>
                </div>
            </main>
        </div>
    );
}
