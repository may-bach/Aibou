import { motion } from 'framer-motion';

interface ThinkingIndicatorProps {
    activeNode: string;
}

export function ThinkingIndicator({ activeNode }: ThinkingIndicatorProps) {
    let displayText = "Thinking";
    const lower = activeNode.toLowerCase();

    if (lower.includes("supervisor")) {
        displayText = "Analyzing request";
    } else if (lower.includes("planner")) {
        displayText = "Designing plan";
    } else if (lower.includes("coder")) {
        displayText = "Writing code";
    } else if (lower.includes("executor")) {
        displayText = "Testing in sandbox";
    } else if (lower.includes("critic")) {
        displayText = "Reviewing output";
    } else if (lower.includes("web_search") || lower.includes("search")) {
        displayText = "Searching the web";
    } else if (lower.includes("calculate") || lower.includes("math")) {
        displayText = "Computing calculation";
    } else if (lower.includes("time") || lower.includes("date")) {
        displayText = "Checking temporal context";
    } else if (lower.includes("file")) {
        displayText = "Inspecting workspace";
    } else if (lower.includes("specialist")) {
        if (lower.includes("finance")) displayText = "Consulting financial model";
        else if (lower.includes("science")) displayText = "Consulting science model";
        else if (lower.includes("creative")) displayText = "Generating creative response";
        else if (lower.includes("reasoning")) displayText = "Reasoning deeply";
        else displayText = "Formulating response";
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
