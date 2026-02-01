'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowLeft, Loader2, Volume2, Play, Download, Mic } from 'lucide-react';
import { AnimatedCard } from '@/components/animations';

export default function TTSPage() {
    const [text, setText] = useState('');
    const [selectedVoice, setSelectedVoice] = useState('th-TH-NiwatNeural');
    const [generatedAudio, setGeneratedAudio] = useState<string | null>(null);

    // Fetch voices
    const { data: voicesData } = useQuery({
        queryKey: ['tts-voices'],
        queryFn: () => apiClient.getTTSVoices(),
    });

    // Generate TTS mutation
    const ttsMutation = useMutation({
        mutationFn: () => apiClient.generateTTS({ text, voice: selectedVoice }),
        onSuccess: (data) => {
            if (data.success && data.audio_path) {
                setGeneratedAudio(data.audio_path);
            }
        },
    });

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-pink-950 to-slate-950">
            {/* Animated sound waves background */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                {[...Array(8)].map((_, i) => (
                    <motion.div
                        key={i}
                        className="absolute left-1/2 top-1/2 h-32 w-32 -translate-x-1/2 -translate-y-1/2 rounded-full border border-pink-500/20"
                        animate={{
                            scale: [1, 3 + i * 0.5, 1],
                            opacity: [0.3, 0, 0.3],
                        }}
                        transition={{
                            duration: 4,
                            repeat: Infinity,
                            delay: i * 0.5,
                            ease: 'easeOut',
                        }}
                    />
                ))}
            </div>

            {/* Header */}
            <header className="relative border-b border-white/10 bg-black/20 backdrop-blur-sm">
                <div className="container mx-auto px-6 py-4">
                    <div className="flex items-center gap-4">
                        <Link href="/" className="rounded-lg p-2 hover:bg-white/10 transition-colors">
                            <ArrowLeft className="h-5 w-5 text-pink-400" />
                        </Link>
                        <div className="flex items-center gap-3">
                            <motion.div
                                animate={{ scale: [1, 1.1, 1] }}
                                transition={{ duration: 1, repeat: Infinity }}
                            >
                                <Volume2 className="h-6 w-6 text-pink-400" />
                            </motion.div>
                            <h1 className="text-xl font-bold text-white">Text-to-Speech Generator</h1>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="relative container mx-auto px-6 py-12">
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="mx-auto max-w-3xl space-y-8"
                >
                    {/* Input Section */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                    >
                        <AnimatedCard className="rounded-2xl border border-pink-500/20 bg-gradient-to-br from-pink-900/40 to-slate-900/40 p-8 backdrop-blur-sm">
                            <div className="space-y-6">
                                {/* Text Input */}
                                <div>
                                    <label className="block text-sm font-medium text-pink-200 mb-2">
                                        <Mic className="inline h-4 w-4 mr-2" />
                                        Text to Convert
                                    </label>
                                    <motion.textarea
                                        whileFocus={{ scale: 1.01, borderColor: 'rgba(236, 72, 153, 0.5)' }}
                                        value={text}
                                        onChange={(e) => setText(e.target.value)}
                                        rows={5}
                                        placeholder="Enter the text you want to convert to speech..."
                                        className="w-full rounded-lg border border-pink-500/30 bg-slate-900/50 px-4 py-3 text-white placeholder-pink-300/40 focus:border-pink-500 focus:outline-none focus:ring-2 focus:ring-pink-500/50 transition-all"
                                    />
                                </div>

                                {/* Voice Selection */}
                                <div>
                                    <label className="block text-sm font-medium text-pink-200 mb-3">
                                        Select Voice
                                    </label>
                                    <div className="grid gap-3 md:grid-cols-2">
                                        {(voicesData?.voices || []).map((voice, idx) => (
                                            <motion.button
                                                key={voice.id}
                                                whileHover={{ scale: 1.02 }}
                                                whileTap={{ scale: 0.98 }}
                                                initial={{ opacity: 0, x: -20 }}
                                                animate={{ opacity: 1, x: 0 }}
                                                transition={{ delay: idx * 0.1 }}
                                                onClick={() => setSelectedVoice(voice.id)}
                                                className={`relative flex items-center gap-3 rounded-xl border p-4 transition-all ${selectedVoice === voice.id
                                                    ? 'border-pink-500 bg-pink-500/20 shadow-lg shadow-pink-500/20'
                                                    : 'border-pink-500/20 bg-slate-800/50 hover:border-pink-500/40'
                                                    }`}
                                            >
                                                {selectedVoice === voice.id && (
                                                    <motion.div
                                                        layoutId="voice-selected"
                                                        className="absolute inset-0 rounded-xl border-2 border-pink-500"
                                                    />
                                                )}
                                                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-pink-500/20">
                                                    <Volume2 className="h-5 w-5 text-pink-400" />
                                                </div>
                                                <div className="text-left">
                                                    <div className="font-medium text-white">{voice.name}</div>
                                                    <div className="text-xs text-pink-200/60 uppercase">{voice.language}</div>
                                                </div>
                                            </motion.button>
                                        ))}
                                    </div>
                                </div>

                                {/* Generate Button */}
                                <motion.button
                                    whileHover={{ scale: 1.02, boxShadow: '0 20px 40px -15px rgba(236, 72, 153, 0.4)' }}
                                    whileTap={{ scale: 0.98 }}
                                    onClick={() => ttsMutation.mutate()}
                                    disabled={ttsMutation.isPending || !text.trim()}
                                    className="w-full rounded-xl bg-gradient-to-r from-pink-600 to-purple-600 px-6 py-4 font-semibold text-white shadow-lg shadow-pink-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3"
                                >
                                    {ttsMutation.isPending ? (
                                        <>
                                            <Loader2 className="h-5 w-5 animate-spin" />
                                            Generating Audio...
                                        </>
                                    ) : (
                                        <>
                                            <Play className="h-5 w-5" />
                                            Generate Audio
                                        </>
                                    )}
                                </motion.button>
                            </div>
                        </AnimatedCard>
                    </motion.div>

                    {/* Result Section */}
                    {generatedAudio && (
                        <motion.div
                            initial={{ opacity: 0, y: 30 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
                        >
                            <AnimatedCard className="rounded-2xl border border-green-500/20 bg-gradient-to-br from-green-900/40 to-slate-900/40 p-8 backdrop-blur-sm">
                                <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-green-400">
                                    <motion.span
                                        animate={{ scale: [1, 1.2, 1] }}
                                        transition={{ duration: 0.5, repeat: 3 }}
                                    >
                                        ✓
                                    </motion.span>
                                    Audio Generated Successfully!
                                </h3>
                                <div className="flex items-center gap-4">
                                    <motion.div
                                        whileHover={{ scale: 1.1 }}
                                        className="flex h-16 w-16 items-center justify-center rounded-full bg-green-500/20"
                                    >
                                        <Volume2 className="h-8 w-8 text-green-400" />
                                    </motion.div>
                                    <div className="flex-1">
                                        <p className="text-sm text-green-200/80">{generatedAudio}</p>
                                        <div className="mt-2 flex gap-2">
                                            <motion.button
                                                whileHover={{ scale: 1.05 }}
                                                whileTap={{ scale: 0.95 }}
                                                className="flex items-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
                                            >
                                                <Download className="h-4 w-4" /> Download
                                            </motion.button>
                                        </div>
                                    </div>
                                </div>
                            </AnimatedCard>
                        </motion.div>
                    )}

                    {/* Error */}
                    {ttsMutation.isError && (
                        <motion.div
                            initial={{ opacity: 0, y: 30 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="rounded-2xl border border-red-500/20 bg-gradient-to-br from-red-900/40 to-slate-900/40 p-6 backdrop-blur-sm"
                        >
                            <p className="text-red-400">
                                {ttsMutation.error instanceof Error ? ttsMutation.error.message : 'Generation failed'}
                            </p>
                        </motion.div>
                    )}
                </motion.div>
            </main>
        </div>
    );
}
