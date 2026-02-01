'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Loader2, BookOpen, Check, FolderOpen, Tag, X } from 'lucide-react';
import { AnimatedCard, Modal } from '@/components/animations';

export default function ObsidianPage() {
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [tags, setTags] = useState<string[]>([]);
    const [tagInput, setTagInput] = useState('');
    const [showSuccess, setShowSuccess] = useState(false);
    const [exportedPath, setExportedPath] = useState('');

    // Check Obsidian status
    const { data: statusData } = useQuery({
        queryKey: ['obsidian-status'],
        queryFn: () => apiClient.getObsidianStatus(),
    });

    // Export mutation
    const exportMutation = useMutation({
        mutationFn: () => apiClient.exportToObsidian({ title, content, tags }),
        onSuccess: (data) => {
            if (data.success) {
                setExportedPath(data.path || '');
                setShowSuccess(true);
                setTitle('');
                setContent('');
                setTags([]);
            }
        },
    });

    const addTag = () => {
        if (tagInput.trim() && !tags.includes(tagInput.trim())) {
            setTags([...tags, tagInput.trim()]);
            setTagInput('');
        }
    };

    const removeTag = (tagToRemove: string) => {
        setTags(tags.filter(t => t !== tagToRemove));
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-violet-950 to-slate-950">
            {/* Animated grid background */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none opacity-30">
                <div className="absolute inset-0" style={{
                    backgroundImage: `linear-gradient(to right, rgba(139, 92, 246, 0.1) 1px, transparent 1px),
                           linear-gradient(to bottom, rgba(139, 92, 246, 0.1) 1px, transparent 1px)`,
                    backgroundSize: '40px 40px',
                }} />
                {[...Array(6)].map((_, i) => (
                    <motion.div
                        key={i}
                        className="absolute h-40 w-40 rounded-lg border border-violet-500/30"
                        animate={{
                            rotate: [0, 90, 180, 270, 360],
                            scale: [1, 1.2, 1],
                            opacity: [0.2, 0.5, 0.2],
                        }}
                        transition={{
                            duration: 20 + i * 5,
                            repeat: Infinity,
                            ease: 'linear',
                        }}
                        style={{
                            left: `${10 + i * 15}%`,
                            top: `${15 + (i % 3) * 25}%`,
                        }}
                    />
                ))}
            </div>

            {/* Header */}
            <header className="relative border-b border-white/10 bg-black/20 backdrop-blur-sm">
                <div className="container mx-auto px-6 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <Link href="/" className="rounded-lg p-2 hover:bg-white/10 transition-colors">
                                <ArrowLeft className="h-5 w-5 text-violet-400" />
                            </Link>
                            <div className="flex items-center gap-3">
                                <motion.div
                                    animate={{ rotateY: [0, 360] }}
                                    transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
                                >
                                    <BookOpen className="h-6 w-6 text-violet-400" />
                                </motion.div>
                                <h1 className="text-xl font-bold text-white">Obsidian Export</h1>
                            </div>
                        </div>
                        {statusData?.configured && (
                            <motion.div
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                className="flex items-center gap-2 rounded-full bg-green-500/20 px-3 py-1 text-sm text-green-400"
                            >
                                <div className="h-2 w-2 rounded-full bg-green-400 animate-pulse" />
                                Vault Connected
                            </motion.div>
                        )}
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="relative container mx-auto px-6 py-12">
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ staggerChildren: 0.1 }}
                    className="mx-auto max-w-3xl space-y-8"
                >
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                    >
                        <AnimatedCard className="rounded-2xl border border-violet-500/20 bg-gradient-to-br from-violet-900/40 to-slate-900/40 p-8 backdrop-blur-sm">
                            <div className="space-y-6">
                                {/* Title Input */}
                                <div>
                                    <label className="block text-sm font-medium text-violet-200 mb-2">
                                        Note Title
                                    </label>
                                    <motion.input
                                        whileFocus={{ scale: 1.01 }}
                                        type="text"
                                        value={title}
                                        onChange={(e) => setTitle(e.target.value)}
                                        placeholder="My Knowledge Note"
                                        className="w-full rounded-lg border border-violet-500/30 bg-slate-900/50 px-4 py-3 text-white placeholder-violet-300/40 focus:border-violet-500 focus:outline-none focus:ring-2 focus:ring-violet-500/50"
                                    />
                                </div>

                                {/* Content Input */}
                                <div>
                                    <label className="block text-sm font-medium text-violet-200 mb-2">
                                        Content (Markdown supported)
                                    </label>
                                    <motion.textarea
                                        whileFocus={{ scale: 1.01 }}
                                        value={content}
                                        onChange={(e) => setContent(e.target.value)}
                                        rows={8}
                                        placeholder="# My Note\n\nWrite your content here..."
                                        className="w-full rounded-lg border border-violet-500/30 bg-slate-900/50 px-4 py-3 text-white placeholder-violet-300/40 focus:border-violet-500 focus:outline-none focus:ring-2 focus:ring-violet-500/50 font-mono text-sm"
                                    />
                                </div>

                                {/* Tags */}
                                <div>
                                    <label className="block text-sm font-medium text-violet-200 mb-2">
                                        <Tag className="inline h-4 w-4 mr-1" /> Tags
                                    </label>
                                    <div className="flex flex-wrap gap-2 mb-3">
                                        <AnimatePresence>
                                            {tags.map((tag) => (
                                                <motion.span
                                                    key={tag}
                                                    initial={{ opacity: 0, scale: 0.8 }}
                                                    animate={{ opacity: 1, scale: 1 }}
                                                    exit={{ opacity: 0, scale: 0.8 }}
                                                    className="flex items-center gap-1 rounded-full bg-violet-500/30 px-3 py-1 text-sm text-violet-200"
                                                >
                                                    #{tag}
                                                    <button onClick={() => removeTag(tag)} className="hover:text-white">
                                                        <X className="h-3 w-3" />
                                                    </button>
                                                </motion.span>
                                            ))}
                                        </AnimatePresence>
                                    </div>
                                    <div className="flex gap-2">
                                        <input
                                            type="text"
                                            value={tagInput}
                                            onChange={(e) => setTagInput(e.target.value)}
                                            onKeyPress={(e) => e.key === 'Enter' && addTag()}
                                            placeholder="Add a tag..."
                                            className="flex-1 rounded-lg border border-violet-500/30 bg-slate-900/50 px-4 py-2 text-white placeholder-violet-300/40 focus:border-violet-500 focus:outline-none"
                                        />
                                        <motion.button
                                            whileHover={{ scale: 1.05 }}
                                            whileTap={{ scale: 0.95 }}
                                            onClick={addTag}
                                            className="rounded-lg bg-violet-600/50 px-4 py-2 text-white hover:bg-violet-600"
                                        >
                                            Add
                                        </motion.button>
                                    </div>
                                </div>

                                {/* Export Button */}
                                <motion.button
                                    whileHover={{ scale: 1.02, boxShadow: '0 20px 40px -15px rgba(139, 92, 246, 0.4)' }}
                                    whileTap={{ scale: 0.98 }}
                                    onClick={() => exportMutation.mutate()}
                                    disabled={exportMutation.isPending || !title.trim() || !content.trim()}
                                    className="w-full rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 px-6 py-4 font-semibold text-white shadow-lg shadow-violet-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3"
                                >
                                    {exportMutation.isPending ? (
                                        <>
                                            <Loader2 className="h-5 w-5 animate-spin" />
                                            Exporting...
                                        </>
                                    ) : (
                                        <>
                                            <FolderOpen className="h-5 w-5" />
                                            Export to Obsidian
                                        </>
                                    )}
                                </motion.button>
                            </div>
                        </AnimatedCard>
                    </motion.div>

                    {/* Vault Info */}
                    {statusData?.vault_path && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                        >
                            <div className="rounded-xl border border-violet-500/10 bg-slate-900/30 p-4 text-sm text-violet-200/60">
                                <FolderOpen className="inline h-4 w-4 mr-2" />
                                Vault: {statusData.vault_path}
                            </div>
                        </motion.div>
                    )}
                </motion.div>
            </main>

            {/* Success Modal */}
            <Modal isOpen={showSuccess} onClose={() => setShowSuccess(false)} title="Export Successful!">
                <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                    className="flex justify-center mb-4"
                >
                    <div className="flex h-16 w-16 items-center justify-center rounded-full bg-green-500/20">
                        <Check className="h-8 w-8 text-green-400" />
                    </div>
                </motion.div>
                <p className="text-center text-gray-300 mb-2">Your note has been exported to:</p>
                <p className="text-center text-sm text-violet-300 font-mono bg-slate-800/50 rounded-lg p-2 mb-4">
                    {exportedPath}
                </p>
                <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setShowSuccess(false)}
                    className="w-full rounded-lg bg-violet-600 px-4 py-2 font-medium text-white hover:bg-violet-700"
                >
                    Close
                </motion.button>
            </Modal>
        </div>
    );
}
