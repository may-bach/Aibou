import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Server, Cloud, Key, CheckCircle2, AlertCircle, Loader2, Eye, EyeOff, Save } from 'lucide-react';



interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSettingsChanged?: () => void;
}

const CLOUD_PRESETS = [
    { id: 'moonshotai/kimi-k3', name: 'Kimi K3 (Moonshot)', desc: 'High-speed creative writing & 1M context ($4.33/M)' },
    { id: 'deepseek/deepseek-chat', name: 'DeepSeek V3', desc: 'Ultra-fast, smart & economical ($0.10/M)' },
    { id: 'anthropic/claude-3.5-sonnet', name: 'Claude 3.5 Sonnet', desc: 'Frontier reasoning & prose ($3.00/M)' },
    { id: 'openai/gpt-4o', name: 'GPT-4o', desc: 'OpenAI flagship multimodal ($2.50/M)' },
];

const LOCAL_PRESETS = [
    { id: 'qwen2.5:14b', name: 'Qwen 2.5 14B', desc: 'Recommended: 50+ tok/s (100% in 16GB VRAM)' },
    { id: 'qwen2.5:7b', name: 'Qwen 2.5 7B', desc: 'Fast & smart: runs on 8GB+ GPUs' },
    { id: 'qwen2.5:3b', name: 'Qwen 2.5 3B', desc: 'Lightweight & instant: runs on any GPU or CPU' },
    { id: 'qwen2.5:1.5b', name: 'Qwen 2.5 1.5B', desc: 'Ultra-compact: minimal RAM usage' },
    { id: 'llama3.2:3b', name: 'Llama 3.2 3B', desc: 'Meta lightweight model' },
    { id: 'llama3.2:1b', name: 'Llama 3.2 1B', desc: 'Tiny 1B model for low-spec PCs' },
    { id: 'hf.co/bartowski/Qwen2.5-32B-Instruct-GGUF:Q3_K_M', name: 'Qwen 2.5 32B (Q3_K_M)', desc: '32B intelligence fit for 16GB GPU' },
];

const API_BASE = 'http://127.0.0.1:8000';

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose, onSettingsChanged }) => {
    const [useLocal, setUseLocal] = useState(true);
    const [apiKey, setApiKey] = useState('');
    const [showKey, setShowKey] = useState(false);
    const [cloudModel, setCloudModel] = useState('moonshotai/kimi-k3');
    const [localModel, setLocalModel] = useState('qwen2.5:14b');
    const [customCloudModel, setCustomCloudModel] = useState('');
    const [isCustomCloud, setIsCustomCloud] = useState(false);
    const [customLocalModel, setCustomLocalModel] = useState('');
    const [isCustomLocal, setIsCustomLocal] = useState(false);

    const [installedModels, setInstalledModels] = useState<string[]>([]);
    const [isTesting, setIsTesting] = useState(false);
    const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
    const [isSaving, setIsSaving] = useState(false);

    // Fetch existing settings and installed Ollama models on open
    useEffect(() => {
        if (!isOpen) {
            setTestResult(null);
            return;
        }

        async function loadConfig() {
            try {
                const res = await fetch(`${API_BASE}/api/v1/config/settings`);
                if (res.ok) {
                    const data = await res.json();
                    setUseLocal(Boolean(data.use_local_llm));
                    if (data.use_local_llm) {
                        const isPreset = LOCAL_PRESETS.some(p => p.id === data.active_chat_model);
                        if (isPreset) {
                            setLocalModel(data.active_chat_model);
                            setIsCustomLocal(false);
                        } else {
                            setCustomLocalModel(data.active_chat_model || '');
                            setIsCustomLocal(true);
                        }
                    } else {
                        const isPreset = CLOUD_PRESETS.some(p => p.id === data.active_chat_model);
                        if (isPreset) {
                            setCloudModel(data.active_chat_model);
                            setIsCustomCloud(false);
                        } else {
                            setCustomCloudModel(data.active_chat_model || '');
                            setIsCustomCloud(true);
                        }
                    }
                }

                // Fetch installed Ollama models
                const localRes = await fetch(`${API_BASE}/api/v1/config/local-models`);
                if (localRes.ok) {
                    const localData = await localRes.json();
                    setInstalledModels(localData.models || []);
                }
            } catch (err) {
                console.warn('Could not load config settings:', err);
            }
        }
        loadConfig();
    }, [isOpen]);


    const handleTestKey = async () => {
        if (!apiKey.trim()) {
            setTestResult({ success: false, message: 'Please enter an OpenRouter API key first.' });
            return;
        }

        setIsTesting(true);
        setTestResult(null);

        const targetModel = isCustomCloud && customCloudModel.trim() ? customCloudModel.trim() : cloudModel;

        try {
            const res = await fetch(`${API_BASE}/api/v1/config/test-key`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: apiKey.trim(), model: targetModel })
            });

            const data = await res.json();
            if (res.ok) {
                setTestResult({ success: true, message: data.message || 'API Key verified and working!' });
            } else {
                setTestResult({ success: false, message: data.detail || 'API key test failed.' });
            }
        } catch (err: any) {
            setTestResult({ success: false, message: `Network error: Ensure Aibou backend is running.` });
        } finally {
            setIsTesting(false);
        }
    };

    const handleSave = async () => {
        setIsSaving(true);
        const targetCloud = isCustomCloud && customCloudModel.trim() ? customCloudModel.trim() : cloudModel;
        const targetLocal = isCustomLocal && customLocalModel.trim() ? customLocalModel.trim() : localModel;

        try {
            const res = await fetch(`${API_BASE}/api/v1/config/save`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    use_local_llm: useLocal,
                    api_key: apiKey.trim() || undefined,
                    cloud_model: targetCloud,
                    local_model: targetLocal
                })
            });

            if (res.ok) {
                if (onSettingsChanged) onSettingsChanged();
                onClose();
            } else {
                const data = await res.json();
                alert(`Error saving: ${data.detail || 'Unknown error'}`);
            }
        } catch (err: any) {
            alert(`Save failed: Could not reach backend server at ${API_BASE}.`);
        } finally {
            setIsSaving(false);
        }
    };

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <div className="settings-backdrop" onClick={onClose}>
                <motion.div
                    className="settings-modal"
                    onClick={(e) => e.stopPropagation()}
                    initial={{ opacity: 0, scale: 0.94, y: 12 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.94, y: 12 }}
                    transition={{ duration: 0.2 }}
                >
                    {/* Header */}
                    <div className="settings-modal__header">
                        <div className="settings-modal__title-group">
                            <span className="settings-modal__title">AI Provider & Model</span>
                            <span className="settings-modal__subtitle">Choose between 100% private local Ollama or high-speed cloud APIs</span>
                        </div>
                        <button className="settings-modal__close-btn" onClick={onClose}>
                            <X size={18} />
                        </button>
                    </div>

                    {/* Mode Toggle Tabs */}
                    <div className="provider-tabs">
                        <button
                            className={`provider-tab ${useLocal ? 'provider-tab--active' : ''}`}
                            onClick={() => { setUseLocal(true); setTestResult(null); }}
                        >
                            <Server size={15} />
                            <span>Local Model (Ollama)</span>
                        </button>
                        <button
                            className={`provider-tab ${!useLocal ? 'provider-tab--active' : ''}`}
                            onClick={() => { setUseLocal(false); setTestResult(null); }}
                        >
                            <Cloud size={15} />
                            <span>Cloud API (OpenRouter)</span>
                        </button>
                    </div>

                    {/* Modal Body */}
                    <div className="settings-modal__body">
                        {useLocal ? (
                            <div className="settings-section">
                                <label className="settings-label">Select Local Ollama Model (1B to 32B)</label>
                                <div className="preset-grid">
                                    {LOCAL_PRESETS.map((p) => {
                                        const isInstalled = installedModels.some(m => m === p.id || m.split(':')[0] === p.id.split(':')[0]);
                                        return (
                                            <div
                                                key={p.id}
                                                className={`preset-card ${!isCustomLocal && localModel === p.id ? 'preset-card--selected' : ''}`}
                                                onClick={() => { setLocalModel(p.id); setIsCustomLocal(false); }}
                                            >
                                                <div className="preset-card__top">
                                                    <span className="preset-card__name">{p.name}</span>
                                                    {isInstalled ? (
                                                        <span className="model-badge model-badge--ready">Installed</span>
                                                    ) : (
                                                        <span className="model-badge model-badge--pull">Needs download</span>
                                                    )}
                                                </div>
                                                <div className="preset-card__desc">{p.desc}</div>
                                            </div>
                                        );
                                    })}
                                    <div
                                        className={`preset-card ${isCustomLocal ? 'preset-card--selected' : ''}`}
                                        onClick={() => setIsCustomLocal(true)}
                                    >
                                        <div className="preset-card__name">Custom Local Model Tag</div>
                                        <div className="preset-card__desc">Type any custom model installed in your Ollama</div>
                                    </div>
                                </div>


                                {isCustomLocal && (
                                    <input
                                        type="text"
                                        className="custom-model-input"
                                        placeholder="e.g. deepseek-r1:7b or phi3:mini or gemma2:2b"
                                        value={customLocalModel}
                                        onChange={(e) => setCustomLocalModel(e.target.value)}
                                        style={{ marginTop: 8 }}
                                    />
                                )}

                                <div className="settings-hint">
                                    Runs locally via Ollama at <code>http://localhost:11434</code> with zero external network calls.
                                </div>
                            </div>
                        ) : (
                            <div className="settings-section">
                                {/* API Key Input */}
                                <label className="settings-label">OpenRouter / OpenAI API Key</label>
                                <div className="api-key-input-row">
                                    <div className="api-key-wrap">
                                        <Key size={14} className="api-key-icon" />
                                        <input
                                            type={showKey ? 'text' : 'password'}
                                            className="api-key-input"
                                            placeholder="sk-or-v1-..."
                                            value={apiKey}
                                            onChange={(e) => setApiKey(e.target.value)}
                                        />
                                        <button
                                            type="button"
                                            className="api-key-eye-btn"
                                            onClick={() => setShowKey(!showKey)}
                                        >
                                            {showKey ? <EyeOff size={14} /> : <Eye size={14} />}
                                        </button>
                                    </div>
                                    <button
                                        type="button"
                                        className="test-key-btn"
                                        onClick={handleTestKey}
                                        disabled={isTesting || !apiKey.trim()}
                                    >
                                        {isTesting ? <Loader2 size={13} className="spin-icon" /> : null}
                                        <span>{isTesting ? 'Testing...' : 'Test Key'}</span>
                                    </button>
                                </div>

                                {/* Test Result Banner */}
                                {testResult && (
                                    <motion.div
                                        className={`test-banner ${testResult.success ? 'test-banner--success' : 'test-banner--error'}`}
                                        initial={{ opacity: 0, y: -4 }}
                                        animate={{ opacity: 1, y: 0 }}
                                    >
                                        {testResult.success ? (
                                            <CheckCircle2 size={15} className="test-banner__icon" />
                                        ) : (
                                            <AlertCircle size={15} className="test-banner__icon" />
                                        )}
                                        <span>{testResult.message}</span>
                                    </motion.div>
                                )}

                                {/* Cloud Model Presets */}
                                <label className="settings-label" style={{ marginTop: 14 }}>Select Cloud Model</label>
                                <div className="preset-grid">
                                    {CLOUD_PRESETS.map((p) => (
                                        <div
                                            key={p.id}
                                            className={`preset-card ${!isCustomCloud && cloudModel === p.id ? 'preset-card--selected' : ''}`}
                                            onClick={() => { setCloudModel(p.id); setIsCustomCloud(false); }}
                                        >
                                            <div className="preset-card__name">{p.name}</div>
                                            <div className="preset-card__desc">{p.desc}</div>
                                        </div>
                                    ))}
                                    <div
                                        className={`preset-card ${isCustomCloud ? 'preset-card--selected' : ''}`}
                                        onClick={() => setIsCustomCloud(true)}
                                    >
                                        <div className="preset-card__name">Custom Model ID</div>
                                        <div className="preset-card__desc">Enter any custom model identifier on OpenRouter</div>
                                    </div>
                                </div>

                                {isCustomCloud && (
                                    <input
                                        type="text"
                                        className="custom-model-input"
                                        placeholder="e.g. meta-llama/llama-3.3-70b-instruct"
                                        value={customCloudModel}
                                        onChange={(e) => setCustomCloudModel(e.target.value)}
                                        style={{ marginTop: 8 }}
                                    />
                                )}
                            </div>
                        )}
                    </div>

                    {/* Footer Actions */}
                    <div className="settings-modal__footer">
                        <button className="settings-btn settings-btn--cancel" onClick={onClose}>
                            Cancel
                        </button>
                        <button className="settings-btn settings-btn--save" onClick={handleSave} disabled={isSaving}>
                            {isSaving ? <Loader2 size={13} className="spin-icon" /> : <Save size={13} />}
                            <span>{isSaving ? 'Saving...' : 'Apply & Save'}</span>
                        </button>
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    );
};
