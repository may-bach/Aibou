import { motion } from 'framer-motion';

export function ThinkingIndicator() {
    return (
        <motion.div
            className="flex items-center gap-1.5 px-4 py-3"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
        >
            <div className="flex items-center gap-[5px] bg-zinc-800 border border-zinc-700/60 rounded-2xl px-4 py-3">
                <span className="text-xs text-zinc-400 mr-2 font-medium">Aibou is thinking</span>
                <span className="thinking-dot w-1.5 h-1.5 rounded-full bg-indigo-400 inline-block" />
                <span className="thinking-dot w-1.5 h-1.5 rounded-full bg-indigo-400 inline-block" />
                <span className="thinking-dot w-1.5 h-1.5 rounded-full bg-indigo-400 inline-block" />
            </div>
        </motion.div>
    );
}
