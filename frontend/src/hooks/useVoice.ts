import { useState, useEffect, useRef, useCallback } from 'react';

export interface VoiceProfile {
    id: string;
    name: string;
    gender: string;
    style: string;
    description: string;
}

export function useVoice() {
    const [isListening, setIsListening] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [currentSpeakingId, setCurrentSpeakingId] = useState<string | null>(null);
    const [selectedVoice, setSelectedVoice] = useState<string>('en-US-ChristopherNeural');
    const [autoVoiceEnabled, setAutoVoiceEnabled] = useState<boolean>(() => {
        return localStorage.getItem('aibou_auto_voice') === 'true';
    });
    const [availableVoices, setAvailableVoices] = useState<VoiceProfile[]>([
        { id: 'en-US-ChristopherNeural', name: 'Christopher', gender: 'Male', style: 'Chill & Confident', description: 'Natural companion tone' },
        { id: 'en-US-GuyNeural', name: 'Guy', gender: 'Male', style: 'Casual Co-Author', description: 'Energetic and conversational' },
        { id: 'en-US-EricNeural', name: 'Eric', gender: 'Male', style: 'Sharp & Direct', description: 'Punchy and clear' },
        { id: 'en-US-JennyNeural', name: 'Jenny', gender: 'Female', style: 'Expressive & Vibrant', description: 'Warm and engaging' },
        { id: 'en-US-AnaNeural', name: 'Ana', gender: 'Female', style: 'Casual & Soft', description: 'Friendly and relaxed' }
    ]);

    const recognitionRef = useRef<any>(null);
    const audioRef = useRef<HTMLAudioElement | null>(null);

    // Save auto-voice setting
    useEffect(() => {
        localStorage.setItem('aibou_auto_voice', String(autoVoiceEnabled));
    }, [autoVoiceEnabled]);

    // Fetch available voices from backend
    useEffect(() => {
        fetch('http://localhost:8000/api/v1/voice/voices')
            .then(res => res.json())
            .then(data => {
                if (data.voices && Array.isArray(data.voices)) {
                    setAvailableVoices(data.voices);
                }
            })
            .catch(() => {
                // Fallback to default list on error
            });
    }, []);

    // Stop speaking immediately
    const stopSpeaking = useCallback(() => {
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.src = '';
            audioRef.current = null;
        }
        setIsSpeaking(false);
        setCurrentSpeakingId(null);
    }, []);

    // Speak given text
    const speak = useCallback((text: string, messageId?: string) => {
        if (!text || !text.trim()) return;

        // If already speaking this message, toggle stop
        if (isSpeaking && currentSpeakingId === messageId) {
            stopSpeaking();
            return;
        }

        stopSpeaking();

        const encodedText = encodeURIComponent(text.slice(0, 4000));
        const url = `http://localhost:8000/api/v1/voice/speak?text=${encodedText}&voice=${selectedVoice}`;

        const audio = new Audio(url);
        audioRef.current = audio;
        setIsSpeaking(true);
        if (messageId) setCurrentSpeakingId(messageId);

        audio.onended = () => {
            setIsSpeaking(false);
            setCurrentSpeakingId(null);
            audioRef.current = null;
        };

        audio.onerror = () => {
            setIsSpeaking(false);
            setCurrentSpeakingId(null);
            audioRef.current = null;
        };

        audio.play().catch(err => {
            console.warn('Audio play prevented or interrupted:', err);
            setIsSpeaking(false);
            setCurrentSpeakingId(null);
        });
    }, [isSpeaking, currentSpeakingId, selectedVoice, stopSpeaking]);

    // Start Speech-to-Text Recognition
    const startListening = useCallback((onResult: (transcript: string) => void) => {
        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

        if (!SpeechRecognition) {
            alert('Speech Recognition is not supported in this browser. Please use Chrome, Edge, or Brave.');
            return;
        }

        stopSpeaking();

        try {
            const recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = 'en-US';

            recognition.onstart = () => {
                setIsListening(true);
            };

            recognition.onresult = (event: any) => {
                let finalTranscript = '';
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        finalTranscript += transcript + ' ';
                    } else {
                        finalTranscript += transcript;
                    }
                }
                if (finalTranscript.trim()) {
                    onResult(finalTranscript);
                }
            };

            recognition.onerror = (event: any) => {
                console.error('Speech recognition error:', event.error);
                setIsListening(false);
            };

            recognition.onend = () => {
                setIsListening(false);
            };

            recognitionRef.current = recognition;
            recognition.start();
        } catch (err) {
            console.error('Error starting speech recognition:', err);
            setIsListening(false);
        }
    }, [stopSpeaking]);

    // Stop Speech-to-Text
    const stopListening = useCallback(() => {
        if (recognitionRef.current) {
            try {
                recognitionRef.current.stop();
            } catch {
                // Ignore error if already stopped
            }
            recognitionRef.current = null;
        }
        setIsListening(false);
    }, []);

    // Toggle Mic Listening
    const toggleListening = useCallback((
        getCurrentText: () => string,
        onUpdateText: (newText: string) => void
    ) => {
        if (isListening) {
            stopListening();
        } else {
            const baseText = getCurrentText();
            startListening((spokenText) => {
                const space = baseText.length > 0 && !baseText.endsWith(' ') ? ' ' : '';
                onUpdateText(baseText + space + spokenText);
            });
        }
    }, [isListening, startListening, stopListening]);

    return {
        isListening,
        isSpeaking,
        currentSpeakingId,
        selectedVoice,
        setSelectedVoice,
        autoVoiceEnabled,
        setAutoVoiceEnabled,
        availableVoices,
        speak,
        stopSpeaking,
        startListening,
        stopListening,
        toggleListening
    };
}
