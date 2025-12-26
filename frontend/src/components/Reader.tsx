import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { ArrowLeft, Play, Pause, Settings, Type, Book } from 'lucide-react';
import Markdown from 'react-markdown';
import './Reader.css'; // We will create this

interface ReaderProps {
    bookId: string;
    onClose: () => void;
}

export function Reader({ bookId, onClose }: ReaderProps) {
    const [content, setContent] = useState('');
    const [loading, setLoading] = useState(true);
    const [isPlaying, setIsPlaying] = useState(false);
    const [fontSize, setFontSize] = useState(18);
    const scrollRef = useRef<HTMLDivElement>(null);
    const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

    useEffect(() => {
        const loadContent = async () => {
            try {
                const res = await axios.get(`http://localhost:8001/api/library/${bookId}/content`);
                setContent(res.data.content);
            } catch (e) {
                setContent("# Error loading book.\nMaybe the file is missing or corrupted.");
            } finally {
                setLoading(false);
            }
        };
        loadContent();
        return () => stopReading();
    }, [bookId]);

    const toggleReading = () => {
        if (isPlaying) {
            stopReading();
        } else {
            startReading();
        }
    };

    const startReading = () => {
        // Very basic implementation: chunks the markdown roughly
        // In prod, you'd strip markdown syntax better.
        const text = content.replace(/[#*`]/g, '');
        const u = new SpeechSynthesisUtterance(text);

        // Attempt to resume from approximate scroll position? (Complex)
        // For MVP, just read from start or current selection

        u.onend = () => setIsPlaying(false);
        window.speechSynthesis.speak(u);
        utteranceRef.current = u;
        setIsPlaying(true);
    };

    const stopReading = () => {
        window.speechSynthesis.cancel();
        setIsPlaying(false);
    };

    return (
        <div className="reader-ui">
            <div className="reader-toolbar">
                <button onClick={onClose}><ArrowLeft size={20} /> Library</button>
                <div className="reader-actions">
                    <button onClick={() => setFontSize(s => Math.max(12, s - 2))}><Type size={14} /></button>
                    <span>{fontSize}px</span>
                    <button onClick={() => setFontSize(s => Math.min(32, s + 2))}><Type size={18} /></button>
                    <div className="sep"></div>
                    <button
                        className={`play-btn ${isPlaying ? 'active' : ''}`}
                        onClick={toggleReading}
                    >
                        {isPlaying ? <Pause size={18} /> : <Play size={18} />}
                        {isPlaying ? 'Stop' : 'Read Aloud'}
                    </button>
                </div>
            </div>

            <div className="reader-viewport" ref={scrollRef}>
                {loading ? (
                    <div className="loading">Loading textual data...</div>
                ) : (
                    <div
                        className="markdown-content prose prose-invert"
                        style={{ fontSize: `${fontSize}px` }}
                    >
                        <Markdown>{content}</Markdown>
                    </div>
                )}
            </div>
        </div>
    );
}
