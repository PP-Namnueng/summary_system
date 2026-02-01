'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type { SummarizeRequest } from '@/lib/types';
import Link from 'next/link';
import { ArrowLeft, Loader2, FileText } from 'lucide-react';

export default function SummarizePage() {
    const [url, setUrl] = useState('');
    const [text, setText] = useState('');
    const [language, setLanguage] = useState<'th' | 'en'>('th');
    const [template, setTemplate] = useState<'standard' | 'executive' | 'technical' | 'eli5'>('standard');

    const summarizeMutation = useMutation({
        mutationFn: (request: SummarizeRequest) => apiClient.summarize(request),
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        summarizeMutation.mutate({ url, text, language, template, model: 'llama3.1' });
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950">
            {/* Header */}
            <header className="border-b border-white/10 bg-black/20 backdrop-blur-sm">
                <div className="container mx-auto px-6 py-4">
                    <div className="flex items-center gap-4">
                        <Link href="/" className="rounded-lg p-2 hover:bg-white/10 transition-colors">
                            <ArrowLeft className="h-5 w-5 text-purple-400" />
                        </Link>
                        <div className="flex items-center gap-3">
                            <FileText className="h-6 w-6 text-purple-400" />
                            <h1 className="text-xl font-bold text-white">Summarize Content</h1>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="container mx-auto px-6 py-12">
                <div className="mx-auto max-w-4xl">
                    {/* Form */}
                    <div className="rounded-2xl border border-purple-500/20 bg-gradient-to-br from-purple-900/40 to-slate-900/40 p-8 backdrop-blur-sm">
                        <form onSubmit={handleSubmit} className="space-y-6">
                            {/* URL Input */}
                            <div>
                                <label htmlFor="url" className="block text-sm font-medium text-purple-200 mb-2">
                                    URL (YouTube or Website)
                                </label>
                                <input
                                    id="url"
                                    type="url"
                                    value={url}
                                    onChange={(e) => setUrl(e.target.value)}
                                    placeholder="https://youtube.com/watch?v=..."
                                    className="w-full rounded-lg border border-purple-500/30 bg-slate-900/50 px-4 py-3 text-white placeholder-purple-300/40 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                                />
                            </div>

                            {/* OR Divider */}
                            <div className="flex items-center gap-4">
                                <div className="h-px flex-1 bg-purple-500/20" />
                                <span className="text-sm text-purple-300/60">OR</span>
                                <div className="h-px flex-1 bg-purple-500/20" />
                            </div>

                            {/* Text Input */}
                            <div>
                                <label htmlFor="text" className="block text-sm font-medium text-purple-200 mb-2">
                                    Direct Text
                                </label>
                                <textarea
                                    id="text"
                                    value={text}
                                    onChange={(e) => setText(e.target.value)}
                                    rows={6}
                                    placeholder="Paste your text here..."
                                    className="w-full rounded-lg border border-purple-500/30 bg-slate-900/50 px-4 py-3 text-white placeholder-purple-300/40 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                                />
                            </div>

                            {/* Options Grid */}
                            <div className="grid gap-4 md:grid-cols-2">
                                {/* Language */}
                                <div>
                                    <label htmlFor="language" className="block text-sm font-medium text-purple-200 mb-2">
                                        Language
                                    </label>
                                    <select
                                        id="language"
                                        value={language}
                                        onChange={(e) => setLanguage(e.target.value as 'th' | 'en')}
                                        className="w-full rounded-lg border border-purple-500/30 bg-slate-900/50 px-4 py-3 text-white focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                                    >
                                        <option value="th">Thai</option>
                                        <option value="en">English</option>
                                    </select>
                                </div>

                                {/* Template */}
                                <div>
                                    <label htmlFor="template" className="block text-sm font-medium text-purple-200 mb-2">
                                        Summary Style
                                    </label>
                                    <select
                                        id="template"
                                        value={template}
                                        onChange={(e) => setTemplate(e.target.value as any)}
                                        className="w-full rounded-lg border border-purple-500/30 bg-slate-900/50 px-4 py-3 text-white focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                                    >
                                        <option value="standard">Standard</option>
                                        <option value="executive">Executive Summary</option>
                                        <option value="technical">Technical</option>
                                        <option value="eli5">ELI5 (Simple)</option>
                                    </select>
                                </div>
                            </div>

                            {/* Submit Button */}
                            <button
                                type="submit"
                                disabled={summarizeMutation.isPending || (!url && !text)}
                                className="w-full rounded-lg bg-purple-600 px-6 py-3 font-medium text-white transition-colors hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                            >
                                {summarizeMutation.isPending ? (
                                    <>
                                        <Loader2 className="h-5 w-5 animate-spin" />
                                        Summarizing...
                                    </>
                                ) : (
                                    'Summarize'
                                )}
                            </button>
                        </form>
                    </div>

                    {/* Results */}
                    {summarizeMutation.data && (
                        <div className="mt-8 rounded-2xl border border-green-500/20 bg-gradient-to-br from-green-900/40 to-slate-900/40 p-8 backdrop-blur-sm">
                            <h2 className="mb-4 text-xl font-bold text-green-400">Summary</h2>
                            {summarizeMutation.data.title && (
                                <h3 className="mb-3 text-lg font-semibold text-white">
                                    {summarizeMutation.data.title}
                                </h3>
                            )}
                            {summarizeMutation.data.success ? (
                                <div className="prose prose-invert max-w-none">
                                    <p className="whitespace-pre-wrap text-green-100/90">
                                        {summarizeMutation.data.summary}
                                    </p>
                                </div>
                            ) : (
                                <p className="text-red-400">Error: {summarizeMutation.data.error}</p>
                            )}
                        </div>
                    )}

                    {/* Error */}
                    {summarizeMutation.isError && (
                        <div className="mt-8 rounded-2xl border border-red-500/20 bg-gradient-to-br from-red-900/40 to-slate-900/40 p-8 backdrop-blur-sm">
                            <h2 className="mb-2 text-xl font-bold text-red-400">Error</h2>
                            <p className="text-red-200">
                                {summarizeMutation.error instanceof Error
                                    ? summarizeMutation.error.message
                                    : 'An error occurred'}
                            </p>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
