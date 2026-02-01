'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { useMutation, useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import { useSettings } from '@/lib/settings-store';
import { Sidebar } from '@/components/Sidebar';
import {
  Brain,
  Link2,
  List,
  FileUp,
  Type,
  Sparkles,
  Radio,
  Zap,
  Search,
  FileText,
  MessageSquare,
  Headphones,
  Library,
  ArrowRight,
} from 'lucide-react';

// Quick navigation cards
const quickNavCards = [
  {
    href: '/sentinel',
    icon: Radio,
    label: 'Sentinel',
    description: 'Automated News Watching',
    buttonLabel: 'Open Sentinel',
    color: '#3b82f6',
  },
  {
    href: '/autopilot',
    icon: Zap,
    label: 'Autopilot',
    description: 'Live AI Observer',
    buttonLabel: 'Open Autopilot',
    color: '#22c55e',
  },
  {
    href: '/research',
    icon: Search,
    label: 'Deep Research',
    description: 'Agentic Web Research',
    buttonLabel: 'Start Research',
    color: '#8b5cf6',
  },
  {
    href: '/summarize',
    icon: FileText,
    label: 'Summary',
    description: 'View Extracted Summaries',
    buttonLabel: 'Go to Summary',
    color: '#6366f1',
  },
  {
    href: '/chat',
    icon: MessageSquare,
    label: 'Chat',
    description: 'Q&A with Context',
    buttonLabel: 'Start Chat',
    color: '#06b6d4',
  },
  {
    href: '/tts',
    icon: Headphones,
    label: 'Podcast',
    description: 'Generate Audio Overview',
    buttonLabel: 'Podcast Studio',
    color: '#ec4899',
  },
];

export default function Home() {
  const { sidebarOpen, selectedModel, contextSize } = useSettings();
  const [inputType, setInputType] = useState<'url' | 'batch' | 'pdf' | 'text'>('url');
  const [inputValue, setInputValue] = useState('');

  // Fetch library stats
  const { data: libraryStats } = useQuery({
    queryKey: ['library-stats'],
    queryFn: () => apiClient.libraryStats(),
  });

  // Summarize mutation
  const summarizeMutation = useMutation({
    mutationFn: async (url: string) => {
      return apiClient.summarize({
        url,
        model: selectedModel,
        contextSize: contextSize,
      });
    },
  });

  const handleExtract = () => {
    if (inputValue.trim()) {
      summarizeMutation.mutate(inputValue);
    }
  };

  return (
    <div className="min-h-screen bg-[#0f1117]">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content */}
      <main
        className={`min-h-screen transition-all duration-300 ${sidebarOpen ? 'pl-[280px]' : 'pl-0'
          }`}
      >
        <div className="max-w-6xl mx-auto px-8 py-8">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-2 mb-12"
          >
            <span className="text-2xl">🏠</span>
            <h1 className="text-xl font-semibold text-white">Welcome Home</h1>
          </motion.div>

          {/* Hero Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-center mb-12"
          >
            {/* Brain icon */}
            <motion.div
              animate={{ y: [0, -8, 0] }}
              transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
              className="inline-flex mb-4"
            >
              <Brain className="h-16 w-16 text-pink-500" />
            </motion.div>

            <h2 className="text-4xl font-bold text-white mb-4">
              Knowledge Summary
            </h2>

            <div className="flex items-center justify-center gap-4 text-sm font-medium tracking-wider">
              <span className="text-red-400">EXTRACT</span>
              <span className="text-white/30">//</span>
              <span className="text-red-400">SUMMARIZE</span>
              <span className="text-white/30">//</span>
              <span className="text-red-400">CHAT</span>
              <span className="text-white/30">//</span>
              <span className="text-red-400">LISTEN</span>
            </div>
          </motion.div>

          {/* Activity Dashboard */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="mb-8"
          >
            <div className="flex items-center gap-2 mb-4">
              <span className="text-lg">📊</span>
              <h3 className="text-sm font-semibold text-white">Your Activity Dashboard</h3>
            </div>

            <div className="grid grid-cols-4 gap-6">
              {[
                { icon: Library, label: 'Library Books', value: libraryStats?.total_documents || 484, color: '#3b82f6', note: '✓ All Indexed' },
                { icon: Search, label: 'Research Reports', value: 0, color: '#8b5cf6' },
                { icon: MessageSquare, label: 'Chat Messages', value: 0, color: '#06b6d4' },
                { icon: FileText, label: 'Summaries', value: 0, color: '#ec4899' },
              ].map((stat, i) => (
                <motion.div
                  key={stat.label}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 + i * 0.05 }}
                  className="space-y-1"
                >
                  <div className="flex items-center gap-2 text-white/50 text-xs">
                    <stat.icon className="h-3.5 w-3.5" style={{ color: stat.color }} />
                    {stat.label}
                  </div>
                  <div className="text-3xl font-bold text-white">{stat.value}</div>
                  {stat.note && (
                    <div className="text-xs text-emerald-400">{stat.note}</div>
                  )}
                </motion.div>
              ))}
            </div>
          </motion.section>

          {/* Quick Start */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mb-12"
          >
            <div className="rounded-2xl border border-white/10 bg-[#151823] p-6">
              <div className="flex items-center gap-2 mb-4">
                <Sparkles className="h-5 w-5 text-pink-500" />
                <h3 className="text-sm font-semibold text-white">Quick Start</h3>
              </div>

              {/* Input type tabs */}
              <div className="flex gap-6 mb-4">
                {[
                  { type: 'url' as const, icon: Link2, label: 'URL', active: true },
                  { type: 'batch' as const, icon: List, label: 'Batch URLs' },
                  { type: 'pdf' as const, icon: FileUp, label: 'PDF' },
                  { type: 'text' as const, icon: Type, label: 'Text' },
                ].map((tab) => (
                  <button
                    key={tab.type}
                    onClick={() => setInputType(tab.type)}
                    className="flex items-center gap-2"
                  >
                    <div
                      className={`w-3 h-3 rounded-full border-2 flex items-center justify-center ${inputType === tab.type ? 'border-red-500' : 'border-white/30'
                        }`}
                    >
                      {inputType === tab.type && (
                        <div className="w-1.5 h-1.5 rounded-full bg-red-500" />
                      )}
                    </div>
                    <tab.icon className={`h-4 w-4 ${inputType === tab.type ? 'text-white' : 'text-white/50'}`} />
                    <span className={`text-sm ${inputType === tab.type ? 'text-white' : 'text-white/50'}`}>
                      {tab.label}
                    </span>
                  </button>
                ))}
              </div>

              {/* Input */}
              <p className="text-xs text-white/40 mb-2">Enter URL (YouTube/Web)</p>
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="https://..."
                className="w-full rounded-lg bg-[#1e2030] border border-white/10 px-4 py-3 text-white placeholder-white/30 focus:border-white/20 focus:outline-none mb-4"
                onKeyDown={(e) => e.key === 'Enter' && handleExtract()}
              />

              {/* Extract button */}
              <motion.button
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                onClick={handleExtract}
                disabled={summarizeMutation.isPending}
                className="w-full rounded-xl bg-gradient-to-r from-red-500 to-rose-500 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-red-500/20 disabled:opacity-50"
              >
                <div className="flex items-center justify-center gap-2">
                  <Sparkles className="h-4 w-4" />
                  Extract & Summarize
                </div>
              </motion.button>
            </div>
          </motion.section>

          {/* Quick Navigation */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <div className="flex items-center gap-2 mb-4">
              <span className="text-lg">🧭</span>
              <h3 className="text-sm font-semibold text-white">Quick Navigation</h3>
            </div>

            <div className="grid grid-cols-3 gap-4">
              {quickNavCards.map((card, i) => (
                <motion.div
                  key={card.href}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 + i * 0.05 }}
                >
                  <Link href={card.href}>
                    <motion.div
                      whileHover={{ y: -4, boxShadow: `0 20px 40px -20px ${card.color}40` }}
                      className="rounded-xl border border-white/10 bg-[#151823] p-5 h-full transition-all"
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <card.icon className="h-5 w-5" style={{ color: card.color }} />
                        <h4 className="font-semibold text-white">{card.label}</h4>
                      </div>
                      <p className="text-xs text-white/50 mb-4">{card.description}</p>
                      <div className="flex items-center justify-between rounded-lg border border-white/10 bg-white/5 px-4 py-2.5">
                        <span className="text-sm text-white/70">{card.buttonLabel}</span>
                        <ArrowRight className="h-4 w-4 text-white/40" />
                      </div>
                    </motion.div>
                  </Link>
                </motion.div>
              ))}
            </div>
          </motion.section>

        </div>
      </main>
    </div>
  );
}
