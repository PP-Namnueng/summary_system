'use client';

import { useState, useRef } from 'react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Loader2, Upload, FileText, Check, CloudUpload, X } from 'lucide-react';
import { AnimatedCard } from '@/components/animations';

export default function UploadPage() {
    const [file, setFile] = useState<File | null>(null);
    const [isDragging, setIsDragging] = useState(false);
    const [uploadResult, setUploadResult] = useState<any>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Upload mutation
    const uploadMutation = useMutation({
        mutationFn: (file: File) => apiClient.uploadPDF(file),
        onSuccess: (data) => {
            if (data.success) {
                setUploadResult(data);
                setFile(null);
            }
        },
    });

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        const droppedFile = e.dataTransfer.files[0];
        if (droppedFile && droppedFile.type === 'application/pdf') {
            setFile(droppedFile);
        }
    };

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0];
        if (selectedFile) {
            setFile(selectedFile);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-cyan-950 to-slate-950">
            {/* Floating upload icons background */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                {[...Array(12)].map((_, i) => (
                    <motion.div
                        key={i}
                        className="absolute text-cyan-500/10"
                        animate={{
                            y: [0, -30, 0],
                            rotate: [0, 10, -10, 0],
                            opacity: [0.1, 0.2, 0.1],
                        }}
                        transition={{
                            duration: 5 + i * 0.5,
                            repeat: Infinity,
                            delay: i * 0.3,
                        }}
                        style={{
                            left: `${5 + i * 8}%`,
                            top: `${10 + (i % 4) * 20}%`,
                        }}
                    >
                        <FileText className="h-12 w-12" />
                    </motion.div>
                ))}
            </div>

            {/* Header */}
            <header className="relative border-b border-white/10 bg-black/20 backdrop-blur-sm">
                <div className="container mx-auto px-6 py-4">
                    <div className="flex items-center gap-4">
                        <Link href="/" className="rounded-lg p-2 hover:bg-white/10 transition-colors">
                            <ArrowLeft className="h-5 w-5 text-cyan-400" />
                        </Link>
                        <div className="flex items-center gap-3">
                            <motion.div
                                animate={{ y: [0, -5, 0] }}
                                transition={{ duration: 2, repeat: Infinity }}
                            >
                                <Upload className="h-6 w-6 text-cyan-400" />
                            </motion.div>
                            <h1 className="text-xl font-bold text-white">Upload PDF to Library</h1>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="relative container mx-auto px-6 py-12">
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="mx-auto max-w-2xl space-y-8"
                >
                    {/* Upload Zone */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                    >
                        <AnimatedCard className="rounded-2xl border border-cyan-500/20 bg-gradient-to-br from-cyan-900/40 to-slate-900/40 p-8 backdrop-blur-sm">
                            {/* Drop Zone */}
                            <motion.div
                                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                                onDragLeave={() => setIsDragging(false)}
                                onDrop={handleDrop}
                                onClick={() => fileInputRef.current?.click()}
                                animate={{
                                    borderColor: isDragging ? 'rgba(6, 182, 212, 0.8)' : 'rgba(6, 182, 212, 0.3)',
                                    backgroundColor: isDragging ? 'rgba(6, 182, 212, 0.1)' : 'transparent',
                                }}
                                className="relative cursor-pointer rounded-xl border-2 border-dashed border-cyan-500/30 p-12 text-center transition-colors hover:border-cyan-500/50"
                            >
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept=".pdf"
                                    onChange={handleFileSelect}
                                    className="hidden"
                                />

                                <motion.div
                                    animate={isDragging ? { scale: 1.1, y: -10 } : { scale: 1, y: 0 }}
                                    transition={{ type: 'spring', stiffness: 300 }}
                                    className="flex flex-col items-center"
                                >
                                    <motion.div
                                        animate={{ y: [0, -8, 0] }}
                                        transition={{ duration: 2, repeat: Infinity }}
                                        className="flex h-20 w-20 items-center justify-center rounded-full bg-cyan-500/20 mb-4"
                                    >
                                        <CloudUpload className="h-10 w-10 text-cyan-400" />
                                    </motion.div>

                                    <p className="text-lg font-medium text-white mb-2">
                                        {isDragging ? 'Drop your PDF here!' : 'Drag & drop your PDF'}
                                    </p>
                                    <p className="text-sm text-cyan-200/60">
                                        or click to browse files
                                    </p>
                                </motion.div>
                            </motion.div>

                            {/* Selected File */}
                            <AnimatePresence>
                                {file && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 20, height: 0 }}
                                        animate={{ opacity: 1, y: 0, height: 'auto' }}
                                        exit={{ opacity: 0, y: -20, height: 0 }}
                                        className="mt-6"
                                    >
                                        <div className="flex items-center justify-between rounded-lg bg-cyan-500/10 p-4">
                                            <div className="flex items-center gap-3">
                                                <FileText className="h-8 w-8 text-cyan-400" />
                                                <div>
                                                    <p className="font-medium text-white">{file.name}</p>
                                                    <p className="text-sm text-cyan-200/60">
                                                        {(file.size / 1024 / 1024).toFixed(2)} MB
                                                    </p>
                                                </div>
                                            </div>
                                            <button
                                                onClick={(e) => { e.stopPropagation(); setFile(null); }}
                                                className="p-2 text-cyan-300 hover:text-white transition-colors"
                                            >
                                                <X className="h-5 w-5" />
                                            </button>
                                        </div>

                                        {/* Upload Button */}
                                        <motion.button
                                            whileHover={{ scale: 1.02, boxShadow: '0 20px 40px -15px rgba(6, 182, 212, 0.4)' }}
                                            whileTap={{ scale: 0.98 }}
                                            onClick={() => uploadMutation.mutate(file)}
                                            disabled={uploadMutation.isPending}
                                            className="mt-4 w-full rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 px-6 py-4 font-semibold text-white shadow-lg shadow-cyan-500/20 transition-all disabled:opacity-50 flex items-center justify-center gap-3"
                                        >
                                            {uploadMutation.isPending ? (
                                                <>
                                                    <Loader2 className="h-5 w-5 animate-spin" />
                                                    Uploading & Processing...
                                                </>
                                            ) : (
                                                <>
                                                    <Upload className="h-5 w-5" />
                                                    Upload to Library
                                                </>
                                            )}
                                        </motion.button>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </AnimatedCard>
                    </motion.div>

                    {/* Success Result */}
                    <AnimatePresence>
                        {uploadResult && (
                            <motion.div
                                initial={{ opacity: 0, y: 30, scale: 0.95 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                exit={{ opacity: 0, y: -30, scale: 0.95 }}
                                transition={{ type: 'spring', stiffness: 300, damping: 25 }}
                            >
                                <AnimatedCard className="rounded-2xl border border-green-500/20 bg-gradient-to-br from-green-900/40 to-slate-900/40 p-8 backdrop-blur-sm">
                                    <div className="flex items-center gap-4 mb-4">
                                        <motion.div
                                            initial={{ scale: 0 }}
                                            animate={{ scale: 1 }}
                                            transition={{ type: 'spring', stiffness: 400, delay: 0.2 }}
                                            className="flex h-14 w-14 items-center justify-center rounded-full bg-green-500/20"
                                        >
                                            <Check className="h-7 w-7 text-green-400" />
                                        </motion.div>
                                        <div>
                                            <h3 className="text-lg font-semibold text-green-400">Upload Successful!</h3>
                                            <p className="text-sm text-green-200/70">{uploadResult.filename}</p>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4 mt-4">
                                        <div className="rounded-lg bg-slate-800/50 p-3 text-center">
                                            <div className="text-2xl font-bold text-cyan-400">{uploadResult.pages || '?'}</div>
                                            <div className="text-xs text-cyan-200/60">Pages</div>
                                        </div>
                                        <div className="rounded-lg bg-slate-800/50 p-3 text-center">
                                            <div className="text-2xl font-bold text-cyan-400">✓</div>
                                            <div className="text-xs text-cyan-200/60">Indexed</div>
                                        </div>
                                    </div>

                                    <motion.button
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                        onClick={() => setUploadResult(null)}
                                        className="mt-6 w-full rounded-lg bg-green-600/30 px-4 py-2 font-medium text-green-300 hover:bg-green-600/50"
                                    >
                                        Upload Another
                                    </motion.button>
                                </AnimatedCard>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Error */}
                    {uploadMutation.isError && (
                        <motion.div
                            initial={{ opacity: 0, y: 30 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="rounded-2xl border border-red-500/20 bg-gradient-to-br from-red-900/40 to-slate-900/40 p-6 backdrop-blur-sm"
                        >
                            <p className="text-red-400">
                                {uploadMutation.error instanceof Error ? uploadMutation.error.message : 'Upload failed'}
                            </p>
                        </motion.div>
                    )}
                </motion.div>
            </main>
        </div>
    );
}
