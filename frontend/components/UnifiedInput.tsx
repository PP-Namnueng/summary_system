'use client';

import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Link2,
    Youtube,
    FileText,
    List,
    Upload,
    Sparkles,
    MessageSquare,
    Search,
    Loader2,
    X,
} from 'lucide-react';

export type InputType = 'url' | 'youtube' | 'pdf' | 'batch';

interface UnifiedInputProps {
    onSubmit: (data: { type: InputType; content: string | File; urls?: string[] }) => void;
    isLoading?: boolean;
}

const inputTypes = [
    { type: 'url' as const, label: 'URL', icon: Link2, color: 'purple' },
    { type: 'youtube' as const, label: 'YouTube', icon: Youtube, color: 'red' },
    { type: 'pdf' as const, label: 'PDF', icon: FileText, color: 'cyan' },
    { type: 'batch' as const, label: 'Batch', icon: List, color: 'amber' },
];

export function UnifiedInput({ onSubmit, isLoading }: UnifiedInputProps) {
    const [activeType, setActiveType] = useState<InputType>('url');
    const [inputValue, setInputValue] = useState('');
    const [batchUrls, setBatchUrls] = useState('');
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [isDragging, setIsDragging] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleSubmit = (action: 'summarize' | 'chat' | 'research') => {
        if (activeType === 'pdf' && selectedFile) {
            onSubmit({ type: 'pdf', content: selectedFile });
        } else if (activeType === 'batch') {
            const urls = batchUrls.split('\n').filter(u => u.trim());
            onSubmit({ type: 'batch', content: batchUrls, urls });
        } else {
            onSubmit({ type: activeType, content: inputValue });
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        const file = e.dataTransfer.files[0];
        if (file?.type === 'application/pdf') {
            setSelectedFile(file);
            setActiveType('pdf');
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) setSelectedFile(file);
    };

    const clearInput = () => {
        setInputValue('');
        setBatchUrls('');
        setSelectedFile(null);
    };

    const hasContent = activeType === 'pdf' ? !!selectedFile :
        activeType === 'batch' ? !!batchUrls.trim() :
            !!inputValue.trim();

    return (
        <div className="w-full max-w-4xl mx-auto">
            {/* Type Tabs */}
            <div className="flex gap-2 mb-4">
                {inputTypes.map((item) => (
                    <motion.button
                        key={item.type}
                        onClick={() => setActiveType(item.type)}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition-all ${activeType === item.type
                                ? `bg-${item.color}-500/20 border border-${item.color}-500/50 text-${item.color}-300`
                                : 'bg-white/5 border border-white/10 text-white/60 hover:bg-white/10'
                            }`}
                        style={{
                            backgroundColor: activeType === item.type ? `var(--${item.color}-bg)` : undefined,
                        }}
                    >
                        <item.icon className="h-4 w-4" />
                        {item.label}
                    </motion.button>
                ))}
            </div>

            {/* Input Area */}
            <motion.div
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleDrop}
                animate={{
                    borderColor: isDragging ? 'rgba(34, 211, 238, 0.5)' : 'rgba(255,255,255,0.1)',
                }}
                className="relative rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-xl overflow-hidden"
            >
                {/* Glow effect */}
                <div className="absolute inset-0 bg-gradient-to-r from-purple-500/5 via-transparent to-blue-500/5 pointer-events-none" />

                <AnimatePresence mode="wait">
                    {activeType === 'pdf' ? (
                        <motion.div
                            key="pdf"
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="p-6"
                        >
                            {selectedFile ? (
                                <div className="flex items-center justify-between p-4 rounded-xl bg-cyan-500/10 border border-cyan-500/30">
                                    <div className="flex items-center gap-3">
                                        <FileText className="h-8 w-8 text-cyan-400" />
                                        <div>
                                            <p className="font-medium text-white">{selectedFile.name}</p>
                                            <p className="text-sm text-cyan-300/70">
                                                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                                            </p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => setSelectedFile(null)}
                                        className="p-2 text-cyan-300 hover:text-white transition-colors"
                                    >
                                        <X className="h-5 w-5" />
                                    </button>
                                </div>
                            ) : (
                                <div
                                    onClick={() => fileInputRef.current?.click()}
                                    className="flex flex-col items-center justify-center py-12 cursor-pointer text-center"
                                >
                                    <motion.div
                                        animate={{ y: [0, -8, 0] }}
                                        transition={{ duration: 2, repeat: Infinity }}
                                        className="mb-4 p-4 rounded-full bg-cyan-500/20"
                                    >
                                        <Upload className="h-8 w-8 text-cyan-400" />
                                    </motion.div>
                                    <p className="text-white font-medium mb-1">Drop PDF here or click to browse</p>
                                    <p className="text-sm text-white/40">Supports .pdf files</p>
                                </div>
                            )}
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept=".pdf"
                                onChange={handleFileChange}
                                className="hidden"
                            />
                        </motion.div>
                    ) : activeType === 'batch' ? (
                        <motion.div
                            key="batch"
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="p-1"
                        >
                            <textarea
                                value={batchUrls}
                                onChange={(e) => setBatchUrls(e.target.value)}
                                placeholder="Enter multiple URLs, one per line...&#10;&#10;https://example.com/article1&#10;https://youtube.com/watch?v=xxx&#10;https://example.com/article2"
                                className="w-full h-40 bg-transparent px-5 py-4 text-white placeholder-white/30 focus:outline-none resize-none"
                            />
                        </motion.div>
                    ) : (
                        <motion.div
                            key="single"
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="p-1"
                        >
                            <input
                                type="text"
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                placeholder={
                                    activeType === 'youtube'
                                        ? 'Paste YouTube URL... (https://youtube.com/watch?v=...)'
                                        : 'Enter URL to summarize... (https://...)'
                                }
                                className="w-full bg-transparent px-5 py-4 text-white placeholder-white/30 focus:outline-none text-lg"
                                onKeyDown={(e) => e.key === 'Enter' && hasContent && !isLoading && handleSubmit('summarize')}
                            />
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Clear button */}
                {hasContent && (
                    <button
                        onClick={clearInput}
                        className="absolute right-4 top-4 p-1.5 rounded-lg text-white/30 hover:text-white/60 hover:bg-white/10 transition-colors"
                    >
                        <X className="h-4 w-4" />
                    </button>
                )}
            </motion.div>

            {/* Action Buttons */}
            <div className="flex gap-3 mt-4">
                <motion.button
                    whileHover={{ scale: 1.02, boxShadow: '0 20px 40px -15px rgba(168, 85, 247, 0.4)' }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => handleSubmit('summarize')}
                    disabled={!hasContent || isLoading}
                    className="flex-1 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-purple-600 to-violet-600 px-6 py-3.5 font-semibold text-white shadow-lg shadow-purple-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {isLoading ? (
                        <Loader2 className="h-5 w-5 animate-spin" />
                    ) : (
                        <Sparkles className="h-5 w-5" />
                    )}
                    Summarize
                </motion.button>

                <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => handleSubmit('chat')}
                    disabled={!hasContent || isLoading}
                    className="flex items-center gap-2 rounded-xl border border-blue-500/30 bg-blue-500/10 px-6 py-3.5 font-medium text-blue-300 transition-all hover:bg-blue-500/20 disabled:opacity-50"
                >
                    <MessageSquare className="h-5 w-5" />
                    Chat
                </motion.button>

                <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => handleSubmit('research')}
                    disabled={!hasContent || isLoading}
                    className="flex items-center gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-6 py-3.5 font-medium text-emerald-300 transition-all hover:bg-emerald-500/20 disabled:opacity-50"
                >
                    <Search className="h-5 w-5" />
                    Research
                </motion.button>
            </div>
        </div>
    );
}
