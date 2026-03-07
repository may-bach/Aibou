import { motion } from 'framer-motion';

interface ThinkingIndicatorProps {
    activeNode: string;
}

export function ThinkingIndicator({ activeNode }: ThinkingIndicatorProps) {
    let displayText = "Thinking";
    switch (activeNode) {
        case "Supervisor":
            displayText = "Analyzing the request";
            break;
        case "Planner":
            displayText = "Building a plan";
            break;
        case "Coder":
            displayText = "Drafting files";
            break;
        case "Executor":
            displayText = "Testing code in sandbox";
            break;
        case "Critic":
            displayText = "Reviewing execution logs";
            break;
        case "Specialist":
            displayText = "Consulting domain expert";
            break;
    }

    return (
        <motion.div
            className="thinking-row"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
        >
            <span className="thinking-label">{displayText}</span>
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
