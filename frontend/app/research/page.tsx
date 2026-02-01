'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type { ResearchRequest } from '@/lib/types';
import Link from 'next/link';
import { ArrowLeft, Loader2, Search } from 'lucide-react';

export default function ResearchPage() {
    const [topic, setTopic] = useState('');
    const [language, setLanguage] = useState<'th' | 'en'>('th');
    const [maxSources, setMaxSources] = useState(5);

    const researchMutation = useMutation({
        mutationFn: (request: ResearchRequest) => apiClient.research(request),
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        researchMutation.mutate({ topic, language, max_sources: maxSources });
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-emerald-950 to-slate-950">
            {/* Header */}
            <header className="border-b border-white/10 bg-black/20 backdrop-blur-sm">
                <div className="container mx-auto px-6 py-4">
                    <div className="flex items-center gap-4">
                        <Link href="/" className="rounded-lg p-2 hover:bg-white/10 transition-colors">
                            <ArrowLeft className="h-5 w-5 text-emerald-400" />
                        </Link>
                        <div className="flex items-center gap-3">
                            <Search className="h-6 w-6 text-emerald-400" />
                            <h1 className="text-xl font-bold text-white">Research Topic</h1>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="container mx-auto px-6 py-12">
                <div className="mx-auto max-w-4xl">
                    {/* Form */}
                    <div className="rounded-2xl border border-emerald-500/20 bg-gradient-to-br from-emerald-900/40 to-slate-900/40 p-8 backdrop-blur-sm">
                        <form onSubmit={handleSubmit} className="space-y-6">
                            {/* Topic Input */}
                            <div>
                                <label htmlFor="topic" className="block text-sm font-medium text-emerald-200 mb-2">
                                    Research Topic
                                </label>
                                <input
                                    id="topic"
                                    type="text"
                                    value={topic}
                                    onChange={(e) => setTopic(e.target.value)}
                                    placeholder="What do you want to research?"
                                    className="w-full rounded-lg border border-emerald-500/30 bg-slate-900/50 px-4 py-3 text-white placeholder-emerald-300/40 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                                />
                            </div>

                            {/* Options Grid */}
                            <div className="grid gap-4 md:grid-cols-2">
                                {/* Language */}
                                <div>
                                    <label htmlFor="language" className="block text-sm font-medium text-emerald-200 mb-2">
                                        Language
                                    </label>
                                    <select
                                        id="language"
                                        value={language}
                                        onChange={(e) => setLanguage(e.target.value as 'th' | 'en')}
                                        className="w-full rounded-lg border border-emerald-500/30 bg-slate-900/50 px-4 py-3 text-white focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                                    >
                                        <option value="th">Thai</option>
                                        <option value="en">English</option>
                                    </select>
                                </div>

                                {/* Max Sources */}
                                <div>
                                    <label htmlFor="maxSources" className="block text-sm font-medium text-emerald-200 mb-2">
                                        Max Sources
                                    </label>
                                    <input
                                        id="maxSources"
                                        type="number"
                                        min="1"
                                        max="10"
                                        value={maxSources}
                                        onChange={(e) => setMaxSources(parseInt(e.target.value))}
                                        className="w-full rounded-lg border border-emerald-500/30 bg-slate-900/50 px-4 py-3 text-white focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                                    />
                                </div>
                            </div>

                            {/* Submit Button */}
                            <button
                                type="submit"
                                disabled={researchMutation.isPending || !topic.trim()}
                                className="w-full rounded-lg bg-emerald-600 px-6 py-3 font-medium text-white transition-colors hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                            >
                                {researchMutation.isPending ? (
                                    <>
                                        <Loader2 className="h-5 w-5 animate-spin" />
                                        Researching...
                                    </>
                                ) : (
                                    'Start Research'
                                )}
                            </button>
                        </form>
                    </div>

                    {/* Results */}
                    {researchMutation.data?.success && (
                        <div className="mt-8 space-y-6">
                            {/* Report */}
                            <div className="rounded-2xl border border-emerald-500/20 bg-gradient-to-br from-emerald-900/40 to-slate-900/40 p-8 backdrop-blur-sm">
                                <h2 className="mb-4 text-xl font-bold text-emerald-400">Research Report</h2>
                                <div className="prose prose-invert max-w-none">
                                    <p className="whitespace-pre-wrap text-emerald-100/90">
                                        {researchMutation.data.report}
                                    </p>
                                </div>
                            </div>

                            {/* Sources */}
                            {researchMutation.data.sources && researchMutation.data.sources.length > 0 && (
                                <div className="rounded-2xl border border-emerald-500/20 bg-gradient-to-br from-emerald-900/40 to-slate-900/40 p-8 backdrop-blur-sm">
                                    <h2 className="mb-4 text-xl font-bold text-emerald-400">Sources</h2>
                                    <div className="space-y-3">
                                        {researchMutation.data.sources.map((source, idx) => (
                                            <div key={idx} className="rounded-lg bg-slate-800/50 p-4">
                                                <a
                                                    href={source.url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="text-emerald-300 hover:text-emerald-200 font-medium"
                                                >
                                                    {source.title}
                                                </a>
                                                {source.snippet && (
                                                    <p className="mt-2 text-sm text-emerald-100/70">{source.snippet}</p>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Error */}
                    {(researchMutation.isError || researchMutation.data?.error) && (
                        <div className="mt-8 rounded-2xl border border-red-500/20 bg-gradient-to-br from-red-900/40 to-slate-900/40 p-8 backdrop-blur-sm">
                            <h2 className="mb-2 text-xl font-bold text-red-400">Error</h2>
                            <p className="text-red-200">
                                {researchMutation.data?.error ||
                                    (researchMutation.error instanceof Error
                                        ? researchMutation.error.message
                                        : 'An error occurred')}
                            </p>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
