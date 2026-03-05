import { motion } from 'framer-motion';

export function ThinkingIndicator() {
    return (
        <motion.div
            className="thinking-row"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
        >
            <span className="thinking-label">Thinking</span>
            {[0, 0.18, 0.36].map((delay, i) => (
                <motion.span
                    key={i}
                    className="thinking-dot"
                    animate={{ y: [0, -5, 0], opacity: [0.4, 1, 0.4] }}
                    transition={{ duration: 1.1, delay, repeat: Infinity, ease: 'easeInOut' }}
                />
            ))}
        </motion.div>
    );
}
