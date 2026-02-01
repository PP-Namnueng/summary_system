'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useMutation, useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { useSettings } from '@/lib/settings-store';
import { Sidebar } from '@/components/Sidebar';
import {
    Radio,
    Plus,
    ChevronRight,
    ChevronDown,
    Rss,
    Globe,
    Play,
    Calendar,
    Clock,
    Trash2,
    ExternalLink,
    Loader2,
    RefreshCw,
    Settings,
    Zap,
} from 'lucide-react';

// Source types
const SOURCE_TYPES = [
    { value: 'rss', label: 'RSS' },
    { value: 'youtube', label: 'YouTube Channel' },
    { value: 'github', label: 'GitHub Trending' },
    { value: 'reddit', label: 'Reddit Subreddit' },
    { value: 'devto', label: 'Dev.to Tag' },
    { value: 'hackernews', label: 'Hacker News' },
];

// Mock active sources for demo
const DEMO_SOURCES = [
    { id: '1', name: 'Google Workspace Developers', type: 'rss', url: 'https://workspaceupdates.googleblog.com/feeds/posts/default', active: true },
    { id: '2', name: 'Medium Nops - AI & Machine Learning', type: 'rss', url: 'https://medium.com/feed/tag/machine-learning', active: true },
    { id: '3', name: 'Hugging Face', type: 'rss', url: 'https://huggingface.co/blog/feed.xml', active: true },
    { id: '4', name: 'ArXiv - AI Papers (cs.CL)', type: 'rss', url: 'https://arxiv.org/rss/cs.CL', active: true },
    { id: '5', name: 'Dev.to - AI', type: 'devto', url: 'https://dev.to/feed/tag/ai', active: true },
    { id: '6', name: 'Dev.to - MLOps', type: 'devto', url: 'https://dev.to/feed/tag/mlops', active: true },
    { id: '7', name: 'Dev.to - NLP', type: 'devto', url: 'https://dev.to/feed/tag/nlp', active: true },
    { id: '8', name: 'Dev.to - LLM', type: 'devto', url: 'https://dev.to/feed/tag/llm', active: true },
    { id: '9', name: 'Dev.to - AI Engineer', type: 'devto', url: 'https://dev.to/feed/tag/aiengineer', active: true },
    { id: '10', name: 'Reddit - LocalLLaMA', type: 'reddit', url: 'https://www.reddit.com/r/LocalLLaMA/.rss', active: true },
    { id: '11', name: 'Reddit - MLOps', type: 'reddit', url: 'https://www.reddit.com/r/mlops/.rss', active: true },
    { id: '12', name: 'Reddit - AI Engineering', type: 'reddit', url: 'https://www.reddit.com/r/AIEngineering/.rss', active: true },
    { id: '13', name: 'Hacker News', type: 'hackernews', url: 'https://hnrss.org/frontpage', active: true },
];

export default function SentinelPage() {
    const { sidebarOpen, sentinelAutopilot, setSentinelAutopilot, sentinelInterval, setSentinelInterval } = useSettings();

    // Form state
    const [sourceName, setSourceName] = useState('');
    const [sourceUrl, setSourceUrl] = useState('');
    const [sourceType, setSourceType] = useState('rss');
    const [customTask, setCustomTask] = useState('');

    // UI state
    const [addSourceOpen, setAddSourceOpen] = useState(true);
    const [activeSourcesOpen, setActiveSourcesOpen] = useState(true);
    const [autoScanOpen, setAutoScanOpen] = useState(true);
    const [expandedSource, setExpandedSource] = useState<string | null>(null);
    const [sources, setSources] = useState(DEMO_SOURCES);
    const [isScanning, setIsScanning] = useState(false);
    const [lastScan, setLastScan] = useState<Date | null>(null);

    // Scan mutation
    const scanMutation = useMutation({
        mutationFn: async () => {
            setIsScanning(true);
            // Simulate scan
            await new Promise(resolve => setTimeout(resolve, 2000));
            return { success: true, newItems: Math.floor(Math.random() * 10) };
        },
        onSuccess: (data) => {
            setIsScanning(false);
            setLastScan(new Date());
        },
        onError: () => {
            setIsScanning(false);
        }
    });

    const handleAddSource = () => {
        if (sourceName && sourceUrl) {
            const newSource = {
                id: Date.now().toString(),
                name: sourceName,
                type: sourceType,
                url: sourceUrl,
                active: true,
            };
            setSources([...sources, newSource]);
            setSourceName('');
            setSourceUrl('');
        }
    };

    const handleDeleteSource = (id: string) => {
        setSources(sources.filter(s => s.id !== id));
    };

    const getSourceIcon = (type: string) => {
        switch (type) {
            case 'rss': return Rss;
            case 'youtube': return Play;
            case 'reddit': return Globe;
            default: return Globe;
        }
    };

    return (
        <div className="min-h-screen bg-[#0f1117]">
            <Sidebar />

            <main className={`min-h-screen transition-all duration-300 ${sidebarOpen ? 'pl-[280px]' : 'pl-0'}`}>
                <div className="max-w-7xl mx-auto px-8 py-8">

                    {/* Header */}
                    <motion.header
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-8"
                    >
                        <div className="flex items-center gap-3 mb-2">
                            <Radio className="h-7 w-7 text-blue-500" />
                            <h1 className="text-2xl font-bold text-white">The Content Sentinel</h1>
                        </div>
                        <p className="text-sm text-white/50">Automated Watching for YouTube & Websites</p>
                    </motion.header>

                    <div className="grid grid-cols-2 gap-8">
                        {/* Left Column - Source Manager */}
                        <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.1 }}
                            className="space-y-6"
                        >
                            {/* Source Manager Header */}
                            <div className="flex items-center gap-2">
                                <Settings className="h-5 w-5 text-white/70" />
                                <h2 className="text-lg font-semibold text-white">Source Manager</h2>
                            </div>

                            {/* Add New Source */}
                            <div className="rounded-xl border border-white/10 bg-[#151823] overflow-hidden">
                                <button
                                    onClick={() => setAddSourceOpen(!addSourceOpen)}
                                    className="flex items-center justify-between w-full px-4 py-3 hover:bg-white/5 transition-colors"
                                >
                                    <div className="flex items-center gap-2">
                                        <Plus className="h-4 w-4 text-green-400" />
                                        <span className="text-sm font-medium text-white">Add New Source</span>
                                    </div>
                                    <ChevronDown className={`h-4 w-4 text-white/40 transition-transform ${addSourceOpen ? 'rotate-180' : ''}`} />
                                </button>

                                <AnimatePresence>
                                    {addSourceOpen && (
                                        <motion.div
                                            initial={{ height: 0, opacity: 0 }}
                                            animate={{ height: 'auto', opacity: 1 }}
                                            exit={{ height: 0, opacity: 0 }}
                                            className="overflow-hidden"
                                        >
                                            <div className="px-4 pb-4 space-y-4">
                                                {/* Source Name */}
                                                <div>
                                                    <label className="block text-xs text-white/50 mb-1.5">Source Name</label>
                                                    <input
                                                        type="text"
                                                        value={sourceName}
                                                        onChange={(e) => setSourceName(e.target.value)}
                                                        placeholder="e.g. TechCrunch"
                                                        className="w-full rounded-lg bg-[#1e2030] border border-white/10 px-3 py-2.5 text-sm text-white placeholder-white/30 focus:border-white/20 focus:outline-none"
                                                    />
                                                </div>

                                                {/* RSS/Channel URL */}
                                                <div>
                                                    <label className="block text-xs text-white/50 mb-1.5">RSS / Channel URL</label>
                                                    <input
                                                        type="text"
                                                        value={sourceUrl}
                                                        onChange={(e) => setSourceUrl(e.target.value)}
                                                        placeholder="https://..."
                                                        className="w-full rounded-lg bg-[#1e2030] border border-white/10 px-3 py-2.5 text-sm text-white placeholder-white/30 focus:border-white/20 focus:outline-none"
                                                    />
                                                </div>

                                                {/* Type */}
                                                <div>
                                                    <label className="block text-xs text-white/50 mb-1.5">Type</label>
                                                    <select
                                                        value={sourceType}
                                                        onChange={(e) => setSourceType(e.target.value)}
                                                        className="w-full rounded-lg bg-[#1e2030] border border-white/10 px-3 py-2.5 text-sm text-white focus:outline-none appearance-none cursor-pointer"
                                                    >
                                                        {SOURCE_TYPES.map((type) => (
                                                            <option key={type.value} value={type.value}>
                                                                {type.label}
                                                            </option>
                                                        ))}
                                                    </select>
                                                </div>

                                                {/* Add Button */}
                                                <motion.button
                                                    whileHover={{ scale: 1.02 }}
                                                    whileTap={{ scale: 0.98 }}
                                                    onClick={handleAddSource}
                                                    disabled={!sourceName || !sourceUrl}
                                                    className="w-full flex items-center justify-center gap-2 rounded-lg bg-[#1e2030] border border-white/10 px-4 py-2.5 text-sm font-medium text-white hover:bg-white/10 transition-colors disabled:opacity-50"
                                                >
                                                    Add Source
                                                </motion.button>
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>

                            {/* Active Sources */}
                            <div className="rounded-xl border border-white/10 bg-[#151823] overflow-hidden">
                                <button
                                    onClick={() => setActiveSourcesOpen(!activeSourcesOpen)}
                                    className="flex items-center justify-between w-full px-4 py-3 hover:bg-white/5 transition-colors"
                                >
                                    <div className="flex items-center gap-2">
                                        <Rss className="h-4 w-4 text-blue-400" />
                                        <span className="text-sm font-medium text-white">Active Sources ({sources.length})</span>
                                    </div>
                                    <ChevronDown className={`h-4 w-4 text-white/40 transition-transform ${activeSourcesOpen ? 'rotate-180' : ''}`} />
                                </button>

                                <AnimatePresence>
                                    {activeSourcesOpen && (
                                        <motion.div
                                            initial={{ height: 0, opacity: 0 }}
                                            animate={{ height: 'auto', opacity: 1 }}
                                            exit={{ height: 0, opacity: 0 }}
                                            className="overflow-hidden"
                                        >
                                            <div className="max-h-[400px] overflow-y-auto">
                                                {sources.map((source, i) => {
                                                    const Icon = getSourceIcon(source.type);
                                                    const isExpanded = expandedSource === source.id;

                                                    return (
                                                        <div key={source.id} className="border-t border-white/5">
                                                            <button
                                                                onClick={() => setExpandedSource(isExpanded ? null : source.id)}
                                                                className="flex items-center justify-between w-full px-4 py-2.5 hover:bg-white/5 transition-colors"
                                                            >
                                                                <div className="flex items-center gap-3">
                                                                    <ChevronRight className={`h-3 w-3 text-white/40 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                                                                    <Icon className="h-4 w-4 text-white/50" />
                                                                    <span className="text-sm text-white/80">{source.name}</span>
                                                                </div>
                                                            </button>

                                                            <AnimatePresence>
                                                                {isExpanded && (
                                                                    <motion.div
                                                                        initial={{ height: 0, opacity: 0 }}
                                                                        animate={{ height: 'auto', opacity: 1 }}
                                                                        exit={{ height: 0, opacity: 0 }}
                                                                        className="overflow-hidden"
                                                                    >
                                                                        <div className="px-4 pb-3 pl-10 space-y-2">
                                                                            <p className="text-xs text-white/40 break-all">{source.url}</p>
                                                                            <div className="flex gap-2">
                                                                                <a
                                                                                    href={source.url}
                                                                                    target="_blank"
                                                                                    rel="noopener noreferrer"
                                                                                    className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300"
                                                                                >
                                                                                    <ExternalLink className="h-3 w-3" />
                                                                                    Open
                                                                                </a>
                                                                                <button
                                                                                    onClick={() => handleDeleteSource(source.id)}
                                                                                    className="flex items-center gap-1 text-xs text-red-400 hover:text-red-300"
                                                                                >
                                                                                    <Trash2 className="h-3 w-3" />
                                                                                    Remove
                                                                                </button>
                                                                            </div>
                                                                        </div>
                                                                    </motion.div>
                                                                )}
                                                            </AnimatePresence>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </motion.div>

                        {/* Right Column - Mission Control */}
                        <motion.div
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.2 }}
                            className="space-y-6"
                        >
                            {/* Mission Control Header */}
                            <div className="flex items-center gap-2">
                                <Zap className="h-5 w-5 text-yellow-400" />
                                <h2 className="text-lg font-semibold text-white">Mission Control</h2>
                            </div>

                            {/* Custom Task Input */}
                            <div className="rounded-xl border border-white/10 bg-[#151823] p-4 space-y-4">
                                <div className="flex items-center gap-2">
                                    <Globe className="h-4 w-4 text-white/50" />
                                    <span className="text-xs text-white/50">Custom task/URL (Optional)</span>
                                    <RefreshCw className="h-3 w-3 text-white/30 ml-auto" />
                                </div>

                                <input
                                    type="text"
                                    value={customTask}
                                    onChange={(e) => setCustomTask(e.target.value)}
                                    placeholder="e.g. Collect trending AI discussions, check hackernews"
                                    className="w-full rounded-lg bg-[#1e2030] border border-white/10 px-3 py-2.5 text-sm text-white placeholder-white/30 focus:border-white/20 focus:outline-none"
                                />

                                {/* Scan Button */}
                                <motion.button
                                    whileHover={{ scale: 1.02, boxShadow: '0 10px 30px -10px rgba(239, 68, 68, 0.4)' }}
                                    whileTap={{ scale: 0.98 }}
                                    onClick={() => scanMutation.mutate()}
                                    disabled={isScanning}
                                    className="w-full flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-red-500 to-rose-500 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-red-500/20 disabled:opacity-70"
                                >
                                    {isScanning ? (
                                        <>
                                            <Loader2 className="h-4 w-4 animate-spin" />
                                            Scanning...
                                        </>
                                    ) : (
                                        <>
                                            <Play className="h-4 w-4" />
                                            Scan for New Updates
                                        </>
                                    )}
                                </motion.button>

                                {/* Last Scan Info */}
                                {lastScan && (
                                    <div className="text-center text-xs text-white/40">
                                        Last scan: {lastScan.toLocaleTimeString()}
                                    </div>
                                )}
                            </div>

                            {/* Stats Cards */}
                            <div className="grid grid-cols-2 gap-4">
                                <div className="rounded-xl border border-white/10 bg-[#151823] p-4">
                                    <div className="flex items-center gap-2 mb-2">
                                        <Rss className="h-4 w-4 text-blue-400" />
                                        <span className="text-xs text-white/50">Active Sources</span>
                                    </div>
                                    <div className="text-2xl font-bold text-white">{sources.length}</div>
                                </div>
                                <div className="rounded-xl border border-white/10 bg-[#151823] p-4">
                                    <div className="flex items-center gap-2 mb-2">
                                        <Clock className="h-4 w-4 text-green-400" />
                                        <span className="text-xs text-white/50">Auto-Scan</span>
                                    </div>
                                    <div className="text-2xl font-bold text-white">
                                        {sentinelAutopilot ? sentinelInterval : 'Off'}
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    </div>

                    {/* Scheduled Scans Section */}
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                        className="mt-8"
                    >
                        <div className="flex items-center gap-2 mb-4">
                            <Calendar className="h-5 w-5 text-purple-400" />
                            <h2 className="text-lg font-semibold text-white">Scheduled Scans</h2>
                        </div>

                        <div className="rounded-xl border border-white/10 bg-[#151823] overflow-hidden">
                            <button
                                onClick={() => setAutoScanOpen(!autoScanOpen)}
                                className="flex items-center justify-between w-full px-4 py-3 hover:bg-white/5 transition-colors"
                            >
                                <div className="flex items-center gap-2">
                                    <Settings className="h-4 w-4 text-white/50" />
                                    <span className="text-sm font-medium text-white">Configure Auto Scan</span>
                                </div>
                                <ChevronDown className={`h-4 w-4 text-white/40 transition-transform ${autoScanOpen ? 'rotate-180' : ''}`} />
                            </button>

                            <AnimatePresence>
                                {autoScanOpen && (
                                    <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: 'auto', opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        className="overflow-hidden"
                                    >
                                        <div className="px-4 pb-4 space-y-4">
                                            {/* Enable Toggle */}
                                            <div className="flex items-center justify-between py-2">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-sm text-white/70">Enable Auto-Scan</span>
                                                    <span className="text-xs text-white/30">ⓘ</span>
                                                </div>
                                                <button
                                                    onClick={() => setSentinelAutopilot(!sentinelAutopilot)}
                                                    className={`relative w-10 h-5 rounded-full transition-colors ${sentinelAutopilot ? 'bg-green-500' : 'bg-[#1e2030]'
                                                        }`}
                                                >
                                                    <motion.div
                                                        animate={{ x: sentinelAutopilot ? 20 : 2 }}
                                                        className="absolute top-0.5 h-4 w-4 rounded-full bg-white shadow-sm"
                                                    />
                                                </button>
                                            </div>

                                            {sentinelAutopilot && (
                                                <motion.div
                                                    initial={{ opacity: 0 }}
                                                    animate={{ opacity: 1 }}
                                                    className="space-y-3"
                                                >
                                                    <p className="text-xs text-white/40">Scan interval</p>
                                                    <div className="flex gap-2">
                                                        {[
                                                            { value: '1h', label: 'Every Hour' },
                                                            { value: '6h', label: 'Every 6 Hours' },
                                                            { value: '24h', label: 'Daily' },
                                                        ].map((opt) => (
                                                            <button
                                                                key={opt.value}
                                                                onClick={() => setSentinelInterval(opt.value as any)}
                                                                className={`flex-1 rounded-lg border px-3 py-2 text-xs font-medium transition-all ${sentinelInterval === opt.value
                                                                        ? 'border-green-500/50 bg-green-500/20 text-green-300'
                                                                        : 'border-white/10 bg-[#1e2030] text-white/60 hover:bg-white/5'
                                                                    }`}
                                                            >
                                                                {opt.label}
                                                            </button>
                                                        ))}
                                                    </div>
                                                </motion.div>
                                            )}

                                            <p className="text-xs text-white/30 pt-2">
                                                {sentinelAutopilot
                                                    ? `Auto-scan is enabled. Next scan in ${sentinelInterval === '1h' ? '~1 hour' : sentinelInterval === '6h' ? '~6 hours' : '~24 hours'}.`
                                                    : 'Enable to set up automatic scanning.'
                                                }
                                            </p>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    </motion.section>

                </div>
            </main>
        </div>
    );
}
