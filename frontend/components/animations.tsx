'use client';

import { motion, AnimatePresence, Variants } from 'framer-motion';
import { ReactNode } from 'react';

// Page transition animation
export const pageVariants: Variants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 },
};

export const pageTransition = {
    type: 'spring',
    stiffness: 260,
    damping: 20,
};

// Card hover animation
export const cardVariants: Variants = {
    initial: { scale: 1 },
    hover: { scale: 1.02 },
    tap: { scale: 0.98 },
};

// Stagger children animation
export const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1,
        },
    },
};

export const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
};

// Modal/popup animation
export const modalVariants: Variants = {
    hidden: { opacity: 0, scale: 0.8, y: 50 },
    visible: { opacity: 1, scale: 1, y: 0 },
    exit: { opacity: 0, scale: 0.8, y: 50 },
};

export const backdropVariants: Variants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
    exit: { opacity: 0 },
};

// Animated page wrapper
export function AnimatedPage({ children }: { children: ReactNode }) {
    return (
        <motion.div
            initial="initial"
            animate="animate"
            exit="exit"
            variants={pageVariants}
            transition={{ type: 'spring' as const, stiffness: 260, damping: 20 }}
        >
            {children}
        </motion.div>
    );
}

// Animated card component
export function AnimatedCard({
    children,
    className = '',
    delay = 0
}: {
    children: ReactNode;
    className?: string;
    delay?: number;
}) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
                type: 'spring',
                stiffness: 260,
                damping: 20,
                delay
            }}
            whileHover={{
                scale: 1.02,
                boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
            }}
            whileTap={{ scale: 0.98 }}
            className={className}
        >
            {children}
        </motion.div>
    );
}

// Modal component with animations
interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    children: ReactNode;
    title?: string;
}

export function Modal({ isOpen, onClose, children, title }: ModalProps) {
    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                    />

                    {/* Modal */}
                    <motion.div
                        className="fixed inset-0 z-50 flex items-center justify-center p-4"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                    >
                        <motion.div
                            className="w-full max-w-lg overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br from-slate-900/95 to-slate-950/95 p-6 shadow-2xl backdrop-blur-xl"
                            initial={{ opacity: 0, scale: 0.8, y: 50 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.8, y: 50 }}
                            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
                            onClick={(e) => e.stopPropagation()}
                        >
                            {title && (
                                <h2 className="mb-4 text-xl font-bold text-white">{title}</h2>
                            )}
                            {children}
                        </motion.div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}

// Success/Error toast animation
export const toastVariants: Variants = {
    hidden: { opacity: 0, x: 100, y: 0 },
    visible: { opacity: 1, x: 0, y: 0 },
    exit: { opacity: 0, x: 100 },
};

// Pulse animation for loading
export function PulseLoader({ color = 'purple' }: { color?: string }) {
    return (
        <motion.div
            className={`h-4 w-4 rounded-full bg-${color}-500`}
            animate={{
                scale: [1, 1.2, 1],
                opacity: [1, 0.5, 1],
            }}
            transition={{
                duration: 1,
                repeat: Infinity,
                ease: 'easeInOut',
            }}
        />
    );
}

// Floating animation for decorative elements
export function FloatingElement({
    children,
    delay = 0
}: {
    children: ReactNode;
    delay?: number;
}) {
    return (
        <motion.div
            animate={{
                y: [0, -10, 0],
            }}
            transition={{
                duration: 3,
                repeat: Infinity,
                ease: 'easeInOut',
                delay,
            }}
        >
            {children}
        </motion.div>
    );
}
