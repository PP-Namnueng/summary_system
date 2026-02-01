'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { apiClient } from '@/lib/api-client';
import {
    useSettings,
    CONTEXT_SIZES,
} from '@/lib/settings-store';

// All available Ollama models
const DEFAULT_MODELS = [
    'kimi-k2.5:cloud',
    'qwen2.5:latest',
    'scb10x/llama3.1-typhoon2-8b-instruct:latest',
    'gemma3:latest',
    'llama3.1:latest',
    'deepseek-r1:latest',
    'mistral:latest',
    'codellama:latest',
];
import {
    ChevronLeft,
    ChevronRight,
    ChevronDown,
    Home,
    Radio,
    Zap,
    Search,
    Library,
    FileText,
    MessageSquare,
    Headphones,
    Link2,
    FileUp,
    Type,
    Sparkles,
    Globe,
    Cpu,
    BookOpen,
    HelpCircle,
} from 'lucide-react';

// Navigation items
const navItems = [
    { href: '/', label: 'Home', icon: Home, color: '#f97316' },
    { href: '/sentinel', label: 'Sentinel', icon: Radio, color: '#3b82f6' },
    { href: '/autopilot', label: 'Autopilot', icon: Zap, color: '#22c55e' },
    { href: '/research', label: 'Deep Research', icon: Search, color: '#8b5cf6' },
    { href: '/library', label: 'Library', icon: Library, color: '#ef4444' },
    { href: '/summarize', label: 'Summary', icon: FileText, color: '#6366f1' },
    { href: '/chat', label: 'Chat', icon: MessageSquare, color: '#06b6d4' },
    { href: '/tts', label: 'Podcast', icon: Headphones, color: '#ec4899' },
];

export function Sidebar() {
    const pathname = usePathname();
    const {
        selectedModel,
        setModel,
        contextSize,
        setContextSize,
        obsidianEnabled,
        setObsidianEnabled,
        sidebarOpen,
        toggleSidebar,
    } = useSettings();

    // Fetch available models
    const { data: modelsData } = useQuery({
        queryKey: ['models'],
        queryFn: () => apiClient.getModels(),
    });

    const [mounted, setMounted] = useState(false);
    const [contentInputOpen, setContentInputOpen] = useState(true);
    const [inputType, setInputType] = useState<'url' | 'pdf' | 'text'>('url');
    const [inputValue, setInputValue] = useState('');
    const [outputLanguage, setOutputLanguage] = useState('TH ภาษาไทย');

    useEffect(() => setMounted(true), []);
    if (!mounted) return null;

    const contextLabel = CONTEXT_SIZES.find(s => s.value === contextSize)?.label || `${Math.round(contextSize / 1024)}K`;

    return (
        <>
            {/* Toggle button when closed */}
            <AnimatePresence>
                {!sidebarOpen && (
                    <motion.button
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        onClick={toggleSidebar}
                        className="fixed left-4 top-4 z-50 flex h-10 w-10 items-center justify-center rounded-xl bg-[#1e2030] text-white/70 hover:bg-[#252838] hover:text-white transition-all shadow-lg"
                    >
                        <ChevronRight className="h-5 w-5" />
                    </motion.button>
                )}
            </AnimatePresence>

            {/* Sidebar */}
            <AnimatePresence>
                {sidebarOpen && (
                    <motion.aside
                        initial={{ x: -280, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        exit={{ x: -280, opacity: 0 }}
                        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                        className="fixed left-0 top-0 z-40 h-screen w-[280px] bg-[#151823] overflow-hidden flex flex-col"
                    >
                        {/* Collapse button */}
                        <button
                            onClick={toggleSidebar}
                            className="absolute right-3 top-3 p-1.5 rounded-lg text-white/40 hover:text-white/70 hover:bg-white/5 transition-colors"
                        >
                            <ChevronLeft className="h-4 w-4" />
                        </button>

                        {/* Scrollable content */}
                        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">

                            {/* Navigation */}
                            <section>
                                <div className="flex items-center gap-2 mb-3">
                                    <span className="text-lg">🧭</span>
                                    <h3 className="text-sm font-semibold text-white">Navigation</h3>
                                </div>
                                <nav className="space-y-1">
                                    {navItems.map((item) => {
                                        const isActive = pathname === item.href;
                                        return (
                                            <Link key={item.href} href={item.href}>
                                                <motion.div
                                                    whileHover={{ x: 4 }}
                                                    className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-all ${isActive
                                                        ? 'bg-white/10'
                                                        : 'hover:bg-white/5'
                                                        }`}
                                                >
                                                    <div
                                                        className="w-2 h-2 rounded-full"
                                                        style={{ backgroundColor: isActive ? item.color : 'transparent', boxShadow: isActive ? `0 0 8px ${item.color}` : 'none' }}
                                                    />
                                                    <item.icon className="h-4 w-4" style={{ color: item.color }} />
                                                    <span className={`text-sm ${isActive ? 'text-white font-medium' : 'text-white/70'}`}>
                                                        {item.label}
                                                    </span>
                                                </motion.div>
                                            </Link>
                                        );
                                    })}
                                </nav>
                            </section>

                            <div className="border-t border-white/5" />

                            {/* Content Input */}
                            <section>
                                <button
                                    onClick={() => setContentInputOpen(!contentInputOpen)}
                                    className="flex items-center justify-between w-full mb-3"
                                >
                                    <div className="flex items-center gap-2">
                                        <span className="text-lg">📥</span>
                                        <h3 className="text-sm font-semibold text-white">Content Input</h3>
                                    </div>
                                    <ChevronDown className={`h-4 w-4 text-white/40 transition-transform ${contentInputOpen ? 'rotate-180' : ''}`} />
                                </button>

                                <AnimatePresence>
                                    {contentInputOpen && (
                                        <motion.div
                                            initial={{ height: 0, opacity: 0 }}
                                            animate={{ height: 'auto', opacity: 1 }}
                                            exit={{ height: 0, opacity: 0 }}
                                            className="space-y-3 overflow-hidden"
                                        >
                                            {/* Input type tabs */}
                                            <div className="flex gap-4">
                                                {[
                                                    { type: 'url' as const, icon: Link2, label: 'URL', color: '#ef4444' },
                                                    { type: 'pdf' as const, icon: FileUp, label: 'PDF', color: '#ffffff' },
                                                    { type: 'text' as const, icon: Type, label: 'Text', color: '#ffffff' },
                                                ].map((tab) => (
                                                    <button
                                                        key={tab.type}
                                                        onClick={() => setInputType(tab.type)}
                                                        className="flex items-center gap-1.5"
                                                    >
                                                        <div
                                                            className={`w-3 h-3 rounded-full border-2 flex items-center justify-center ${inputType === tab.type ? 'border-red-500' : 'border-white/30'
                                                                }`}
                                                        >
                                                            {inputType === tab.type && (
                                                                <div className="w-1.5 h-1.5 rounded-full bg-red-500" />
                                                            )}
                                                        </div>
                                                        <tab.icon className="h-3.5 w-3.5" style={{ color: inputType === tab.type ? tab.color : 'rgba(255,255,255,0.5)' }} />
                                                        <span className={`text-xs ${inputType === tab.type ? 'text-white' : 'text-white/50'}`}>
                                                            {tab.label}
                                                        </span>
                                                    </button>
                                                ))}
                                            </div>

                                            {/* Input label */}
                                            <p className="text-xs text-white/50">URL (YouTube/Web)</p>

                                            {/* Input field */}
                                            <input
                                                type="text"
                                                value={inputValue}
                                                onChange={(e) => setInputValue(e.target.value)}
                                                placeholder="https://..."
                                                className="w-full rounded-lg bg-[#1e2030] border border-white/10 px-3 py-2.5 text-sm text-white placeholder-white/30 focus:border-white/20 focus:outline-none transition-colors"
                                            />

                                            {/* Extract button */}
                                            <motion.button
                                                whileHover={{ scale: 1.02 }}
                                                whileTap={{ scale: 0.98 }}
                                                className="w-full flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-red-500 to-rose-500 px-4 py-2.5 text-sm font-medium text-white shadow-lg shadow-red-500/20"
                                            >
                                                <Sparkles className="h-4 w-4" />
                                                Extract
                                            </motion.button>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </section>

                            <div className="border-t border-white/5" />

                            {/* Settings */}
                            <section className="space-y-4">
                                <div className="flex items-center gap-2">
                                    <span className="text-lg">⚙️</span>
                                    <h3 className="text-sm font-semibold text-white">Settings</h3>
                                </div>

                                {/* Output Language */}
                                <div className="space-y-2">
                                    <div className="flex items-center gap-2">
                                        <Globe className="h-4 w-4 text-blue-400" />
                                        <span className="text-xs text-white/60">Output Language</span>
                                    </div>
                                    <select
                                        value={outputLanguage}
                                        onChange={(e) => setOutputLanguage(e.target.value)}
                                        className="w-full rounded-lg bg-[#1e2030] border border-white/10 px-3 py-2.5 text-sm text-white focus:outline-none appearance-none cursor-pointer"
                                    >
                                        <option value="TH ภาษาไทย">TH ภาษาไทย</option>
                                        <option value="EN English">EN English</option>
                                        <option value="ZH 中文">ZH 中文</option>
                                        <option value="JA 日本語">JA 日本語</option>
                                    </select>
                                </div>

                                {/* AI Model */}
                                <div className="space-y-2">
                                    <div className="flex items-center gap-2">
                                        <Cpu className="h-4 w-4 text-purple-400" />
                                        <span className="text-xs text-white/60">AI Model</span>
                                    </div>
                                    <p className="text-xs text-white/40 -mt-1">Select Model</p>
                                    <select
                                        value={selectedModel}
                                        onChange={(e) => setModel(e.target.value)}
                                        className="w-full rounded-lg bg-[#1e2030] border border-white/10 px-3 py-2.5 text-sm text-white focus:outline-none appearance-none cursor-pointer"
                                    >
                                        {(modelsData?.models || DEFAULT_MODELS).map((model: string) => (
                                            <option key={model} value={model}>
                                                {model}
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                {/* Context Tokens */}
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between">
                                        <span className="text-xs text-white/60">Context (Tokens)</span>
                                        <HelpCircle className="h-3.5 w-3.5 text-white/30" />
                                    </div>
                                    <div className="text-sm font-medium text-red-400">{contextSize.toLocaleString()}</div>
                                    <input
                                        type="range"
                                        min={1024}
                                        max={262144}
                                        step={1024}
                                        value={contextSize}
                                        onChange={(e) => setContextSize(parseInt(e.target.value))}
                                        className="w-full h-1.5 rounded-full bg-[#1e2030] appearance-none cursor-pointer accent-red-500"
                                        style={{
                                            background: `linear-gradient(to right, #ef4444 0%, #ef4444 ${((contextSize - 1024) / (262144 - 1024)) * 100}%, #1e2030 ${((contextSize - 1024) / (262144 - 1024)) * 100}%, #1e2030 100%)`
                                        }}
                                    />
                                    <div className="flex justify-between text-xs text-white/40">
                                        <span>1K</span>
                                        <span>256K</span>
                                    </div>
                                </div>
                            </section>

                            <div className="border-t border-white/5" />

                            {/* Obsidian */}
                            <section className="space-y-3">
                                <div className="flex items-center gap-2">
                                    <BookOpen className="h-4 w-4 text-violet-400" />
                                    <h3 className="text-sm font-semibold text-white">Obsidian</h3>
                                </div>

                                <label className="flex items-center gap-3 cursor-pointer">
                                    <button
                                        onClick={() => setObsidianEnabled(!obsidianEnabled)}
                                        className={`relative w-10 h-5 rounded-full transition-colors ${obsidianEnabled ? 'bg-violet-500' : 'bg-[#1e2030]'
                                            }`}
                                    >
                                        <motion.div
                                            animate={{ x: obsidianEnabled ? 20 : 2 }}
                                            className="absolute top-0.5 h-4 w-4 rounded-full bg-white shadow-sm"
                                        />
                                    </button>
                                    <span className="text-sm text-white/70">Enable</span>
                                </label>
                            </section>

                        </div>
                    </motion.aside>
                )}
            </AnimatePresence>
        </>
    );
}
