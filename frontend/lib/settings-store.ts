'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Settings {
    // Model settings
    selectedModel: string;
    contextSize: number;

    // Obsidian settings
    obsidianEnabled: boolean;
    obsidianPath: string;

    // Podcast settings
    podcastTone: 'professional' | 'casual' | 'educational' | 'storytelling';
    podcastFollowSummary: boolean;

    // TTS settings
    ttsVoice: string;

    // Sentinel settings
    sentinelAutopilot: boolean;
    sentinelInterval: '1h' | '6h' | '24h';

    // UI state
    sidebarOpen: boolean;
}

interface SettingsStore extends Settings {
    setModel: (model: string) => void;
    setContextSize: (size: number) => void;
    setObsidianEnabled: (enabled: boolean) => void;
    setObsidianPath: (path: string) => void;
    setPodcastTone: (tone: Settings['podcastTone']) => void;
    setPodcastFollowSummary: (follow: boolean) => void;
    setTtsVoice: (voice: string) => void;
    setSentinelAutopilot: (enabled: boolean) => void;
    setSentinelInterval: (interval: Settings['sentinelInterval']) => void;
    toggleSidebar: () => void;
    setSidebarOpen: (open: boolean) => void;
}

export const useSettings = create<SettingsStore>()(
    persist(
        (set) => ({
            // Default values
            selectedModel: 'gemma3:latest',
            contextSize: 4096,
            obsidianEnabled: false,
            obsidianPath: '',
            podcastTone: 'professional',
            podcastFollowSummary: true,
            ttsVoice: 'th-TH-NiwatNeural',
            sentinelAutopilot: false,
            sentinelInterval: '1h',
            sidebarOpen: true,

            // Actions
            setModel: (model) => set({ selectedModel: model }),
            setContextSize: (size) => set({ contextSize: size }),
            setObsidianEnabled: (enabled) => set({ obsidianEnabled: enabled }),
            setObsidianPath: (path) => set({ obsidianPath: path }),
            setPodcastTone: (tone) => set({ podcastTone: tone }),
            setPodcastFollowSummary: (follow) => set({ podcastFollowSummary: follow }),
            setTtsVoice: (voice) => set({ ttsVoice: voice }),
            setSentinelAutopilot: (enabled) => set({ sentinelAutopilot: enabled }),
            setSentinelInterval: (interval) => set({ sentinelInterval: interval }),
            toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
            setSidebarOpen: (open) => set({ sidebarOpen: open }),
        }),
        {
            name: 'knowledge-settings',
        }
    )
);

// Context size presets for the slider
export const CONTEXT_SIZES = [
    { value: 1024, label: '1K' },
    { value: 2048, label: '2K' },
    { value: 4096, label: '4K' },
    { value: 8192, label: '8K' },
    { value: 16384, label: '16K' },
    { value: 32768, label: '32K' },
    { value: 65536, label: '64K' },
    { value: 131072, label: '128K' },
    { value: 262144, label: '256K' },
];

export const PODCAST_TONES = [
    { value: 'professional', label: 'Professional', icon: '👔' },
    { value: 'casual', label: 'Casual', icon: '😊' },
    { value: 'educational', label: 'Educational', icon: '📚' },
    { value: 'storytelling', label: 'Storytelling', icon: '📖' },
];

export const SENTINEL_INTERVALS = [
    { value: '1h', label: 'Every Hour' },
    { value: '6h', label: 'Every 6 Hours' },
    { value: '24h', label: 'Daily' },
];
